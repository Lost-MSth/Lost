import logging
import time

from python_sdk import SimulationClient

# 配置日志记录
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- 策略参数 ---
# 阶段切换 Tick
ACCUMULATE_END_TICK = 1000
PUMP_END_TICK = 1900
DISTRIBUTE_START_TICK = 2000
FINAL_LIQUIDATION_TICK = 7000

# 价格目标
TARGET_BUY_PRICE = 92.0
TARGET_SELL_PRICE = 108.0
SUPPORT_PRICE_TRIGGER = 100.0

# 头寸目标与订单大小
TARGET_STOCK_POSITION = 80000
ACCUMULATION_CHUNK_SIZE = 2000
DISTRIBUTION_CHUNK_SIZE = 1000
SUPPORT_CHUNK_SIZE = 800

# 新闻发布节奏
NEGATIVE_NEWS_TICKS = [10, 50, 100, 150, 200]
POSITIVE_NEWS_TICKS = [1600, 1650, 1700, 1750, 1800]


class StrategyState:
    def __init__(self):
        self.flags_claimed = {1: False, 2: False, 3: False}
        self.news_sent = set()
        self.current_phase = "INIT"
        self.last_order_tick = 0


def main():
    client = SimulationClient(
        base_url="https://prob10-eg6uhzdh.geekgame.pku.edu.cn/")
    # client = SimulationClient(base_url="http://127.0.0.1:8080")
    state = StrategyState()

    try:
        client.start()
        if not client.wait_until_connected(timeout=10):
            logging.error("无法连接到模拟服务器。")
            return
        logging.info("已成功连接到服务器。")

        try:
            client.start_simulation()
        except Exception as e:
            if "already_running" in str(e):
                logging.warning("模拟已经在运行中。")
            else:
                raise

        # client.set_tick_duration(0.01)
        # 题目环境只能用一倍速
        client.set_tick_duration(0.1)

        while True:
            event = client.get_event(timeout=10)
            if not event or event.get("type") != "tick_update":
                if not client.state.connected:
                    logging.error("连接断开，退出策略。")
                    break
                continue

            current_tick, last_price = event.get(
                "tick", 0), event.get("last_price", 100.0)

            # 获取完整的 portfolio 信息
            user_data = client.list_user_orders()
            portfolio = user_data.get('portfolio', {})
            cash_total = portfolio.get('cash_total', 0)
            stock_total = portfolio.get('stock_total', 0)
            cash_available = portfolio.get('cash_available', 0)
            stock_available = portfolio.get('stock_available', 0)

            if current_tick >= 9000:
                logging.info("模拟结束。")
                break
            if current_tick <= state.last_order_tick:
                continue

            log_status(current_tick, last_price, cash_total,
                       stock_total, state.current_phase)

            # --- 核心策略状态机 ---

            # 阶段 1 & 2: 吸筹与拉升
            if current_tick < DISTRIBUTE_START_TICK:
                phase_props = {
                    "ACCUMULATE": (ACCUMULATE_END_TICK, NEGATIVE_NEWS_TICKS, -1.0, "负面", TARGET_BUY_PRICE, 0.05),
                    "PUMP": (PUMP_END_TICK, POSITIVE_NEWS_TICKS, 1.0, "正面", float('inf'), 0.1)
                }
                current_phase_key = "PUMP" if current_tick >= ACCUMULATE_END_TICK else "ACCUMULATE"
                state.current_phase = current_phase_key
                _, news_ticks, rating, news_type, price_cond, price_offset = phase_props[
                    current_phase_key]

                broadcast_news(client, state, current_tick,
                               news_ticks, rating, news_type)
                if last_price < price_cond and stock_total < TARGET_STOCK_POSITION:
                    price = get_best_ask(event) + price_offset
                    # <<< 关键检查: 确保有足够可用现金
                    if cash_available >= price * ACCUMULATION_CHUNK_SIZE:
                        client.submit_user_order(
                            "buy", ACCUMULATION_CHUNK_SIZE, price)
                        logging.info(
                            f"Tick {current_tick}: {current_phase_key}阶段, 买入 {ACCUMULATION_CHUNK_SIZE} @{price:.2f}")
                        state.last_order_tick = current_tick

            # 阶段 3: 主动价格管理与动态分销
            elif current_tick < FINAL_LIQUIDATION_TICK:
                state.current_phase = "MAINTAIN_&_DISTRIBUTE"

                orders_cancelled = cancel_all_open_orders(
                    client, user_data.get('open_orders', []), 'sell')
                orders_cancelled = cancel_all_open_orders(
                    client, user_data.get('open_orders', []), 'buy') + orders_cancelled
                if orders_cancelled > 0:
                    logging.info(
                        f"Tick {current_tick}: 清理了 {orders_cancelled} 个过时的卖单。")
                    user_data = client.list_user_orders()
                    portfolio = user_data.get('portfolio', {})
                    cash_available = portfolio.get('cash_available', 0)
                    stock_available = portfolio.get('stock_available', 0)
                    stock_total = portfolio.get('stock_total', 0)

                stock_total = client.state.portfolio.get('stock_total', 0)

                price_now = client.state.last_price
                if stock_total >= 0:
                    if last_price < SUPPORT_PRICE_TRIGGER:
                        # cancel_all_open_orders_new(client)
                        price_to_buy = price_now + 0.01
                        # <<< 关键检查: 确保有足够可用现金进行护盘
                        cash_available = client.state.portfolio.get(
                            'cash_total', 0)
                        if cash_available > price_to_buy * SUPPORT_CHUNK_SIZE:
                            try:
                                client.submit_user_order(
                                    "buy", SUPPORT_CHUNK_SIZE, price_to_buy)
                            except Exception as e:
                                logging.error(
                                    f"Tick {current_tick}: 护盘操作失败: {e}")
                            logging.warning(
                                f"Tick {current_tick}: 护盘操作, 买入 {SUPPORT_CHUNK_SIZE} @{price_to_buy:.2f}")
                            state.last_order_tick = current_tick
                    elif last_price > TARGET_SELL_PRICE:
                        # <<< 关键检查: 卖出数量不能超过可用股票
                        # cancel_all_open_orders_new(client)
                        sell_quantity = min(
                            stock_available, DISTRIBUTION_CHUNK_SIZE)
                        if sell_quantity > 0:
                            price_to_sell = price_now
                            client.submit_user_order(
                                "sell", sell_quantity, price_to_sell)
                            logging.info(
                                f"Tick {current_tick}: 分销 {sell_quantity} 股 @{price_to_sell:.2f}")
                            state.last_order_tick = current_tick

            # 阶段 4: 最终清仓
            else:
                state.current_phase = "FINAL_LIQUIDATION"
                if stock_total > 0:
                    cancel_all_open_orders(
                        client, user_data.get('open_orders', []), 'ANY')
                    user_data = client.list_user_orders()  # 刷新状态
                    stock_available = user_data.get(
                        'portfolio', {}).get('stock_available', 0)
                    # <<< 关键检查: 确保有可用股票可卖
                    if stock_available > 0:
                        price_to_sell = client.state.last_price - 0.5
                        client.submit_user_order(
                            "sell", stock_available, price_to_sell)
                        logging.info(
                            f"Tick {current_tick}: 最终清仓, 卖出剩余 {stock_available} 股。")
                        state.last_order_tick = current_tick + 10

            check_and_get_flags(
                client, client.state.portfolio.get('cash_total', 0), state)

    except KeyboardInterrupt:
        logging.info("手动中断策略。")
    except Exception as e:
        logging.error(f"策略执行时发生错误: {e}", exc_info=True)
    finally:
        client.stop()
        logging.info("客户端已停止。")


def cancel_all_open_orders(client: SimulationClient, open_orders: list, direction: str) -> int:
    cancelled_count = 0
    if not open_orders:
        return 0
    for order in open_orders:
        if direction == 'ANY' or order['direction'] == direction:
            try:
                client.cancel_user_order(order['order_id'])
                cancelled_count += 1
            except Exception:
                pass
    return cancelled_count


def broadcast_news(client, state, tick, news_ticks, rating, news_type):
    for t in news_ticks:
        if tick >= t and t not in state.news_sent:
            client.send_truth(rating)
            state.news_sent.add(t)
            logging.info(f"Tick {tick}: 发送{news_type}新闻。")
            break


def get_best_ask(event: dict) -> float:
    sell_orders = event.get('order_book', {}).get('sell_orders', [])
    return sell_orders[0]['price'] if sell_orders else event.get('last_price', 100.0) * 1.005


def get_best_bid(event: dict) -> float:
    buy_orders = event.get('order_book', {}).get('buy_orders', [])
    return buy_orders[0]['price'] if buy_orders else event.get('last_price', 100.0) * 0.995


def log_status(tick, price, cash, stock, phase):
    logging.info(
        f"Tick: {tick:04d} | Phase: {phase:<22} | Price: {price:7.2f} | Cash: {cash:10.2f} | Stock: {stock:6d} | Value: {(cash + stock * price):10.2f}")


def check_and_get_flags(client: SimulationClient, total_cash: float, state: StrategyState):
    flag_targets = {6000000: 1, 7500000: 2, 9000000: 3}
    for target_cash, flag_id in flag_targets.items():
        if total_cash >= target_cash and not state.flags_claimed[flag_id]:
            try:
                response = client._get("/user/getflag")
                logging.info(f"现金达到 {target_cash}, 获取 Flag 响应: {response}")
                state.flags_claimed[flag_id] = True
            except Exception as e:
                logging.error(f"获取 Flag {flag_id} 失败: {e}")


def cancel_all_open_orders_new(client: SimulationClient):
    """Crucial for ensuring a clean slate before each strategic phase."""
    try:
        orders_info = client.list_user_orders()
        open_orders = orders_info.get('open_orders', [])
        if open_orders:
            print("🧹 Cleaning slate: Cancelling outstanding orders...")
            for order in open_orders:
                client.cancel_user_order(order['order_id'])
    except Exception as e:
        print(f"  - Warning: Could not cancel orders: {e}")


if __name__ == "__main__":
    main()
