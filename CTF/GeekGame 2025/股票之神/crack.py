import time
import logging
from python_sdk import SimulationClient

# 配置日志，方便观察策略执行过程
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_current_tick_and_price(client: SimulationClient):
    """从事件队列中获取最新的 tick 更新"""
    event = None
    # 持续从队列中获取事件，直到找到 tick_update 类型的事件
    while not event or event.get("type") != "tick_update":
        event = client.get_event(timeout=5)
        if not event:
            logging.warning("获取事件超时，可能模拟已结束或未运行")
            return None, None
    return event['tick'], event.get('last_price')


def get_portfolio(client: SimulationClient):
    """获取当前投资组合信息"""
    try:
        return client.list_user_orders().get('portfolio', {})
    except Exception as e:
        logging.error(f"获取投资组合失败: {e}")
        return {}


def main():
    # --- 1. 初始化和准备 ---
    API_BASE_URL = "http://127.0.0.1:8080"  # 根据实际情况修改
    client = SimulationClient(base_url=API_BASE_URL)
    client.start()
    if not client.wait_until_connected(timeout=10):
        logging.error("连接 WebSocket 失败！")
        return

    logging.info("连接成功，开始模拟...")
    try:
        client.start_simulation()
    except Exception as e:
        logging.info(f"模拟已在运行中: {e}")

    # 将模拟速度调至最快，以节约时间
    client.set_tick_duration(0.01)
    logging.info("模拟速度已设置为最快 (10x)")

    time.sleep(2)  # 等待模拟开始和价格稳定

    # --- 2. 吸筹阶段 (Accumulation) ---
    logging.info(">>> 开始执行阶段一：吸筹...")

    # 策略参数
    INITIAL_CASH = 5_000_000.0
    CASH_FOR_BUY_RATIO = 0.95  # 使用95%的现金用于购买股票
    TARGET_SPENT_CASH = INITIAL_CASH * CASH_FOR_BUY_RATIO

    cash_spent = 0
    stock_held = 0

    # 获取一个基准价格
    _, baseline_price = get_current_tick_and_price(client)
    if not baseline_price:
        logging.error("无法获取初始基准价格")
        return
    logging.info(f"获取到市场基准价: {baseline_price:.2f}")

    while cash_spent < TARGET_SPENT_CASH:
        current_tick, last_price = get_current_tick_and_price(client)
        if current_tick is None or current_tick > 8000:  # 如果时间太晚，则停止
            logging.warning("时间不足，提前结束吸筹")
            break

        # 为确保成交，以略高于最新价格的价格买入
        buy_price = last_price * 1.005
        # 每次购买少量，避免对市场造成过大冲击
        quantity_to_buy = 100

        # 检查是否有足够现金
        portfolio = get_portfolio(client)
        available_cash = portfolio.get('cash_available', 0)

        if available_cash < buy_price * quantity_to_buy:
            logging.warning("现金不足，无法继续购买")
            break

        try:
            client.submit_user_order(
                direction="buy",
                quantity=quantity_to_buy,
                price=buy_price,
                immediate_cancel=True
            )
            # cash_spent += buy_price * quantity_to_buy
            # stock_held += quantity_to_buy
            portfolio = get_portfolio(client)
            cash_spent = INITIAL_CASH - portfolio.get('cash_available', 0)
            stock_held = portfolio.get('stock_total', 0)
            logging.info(f"[Tick {current_tick}] 吸筹: 购买 {quantity_to_buy} 股 @ {buy_price:.2f} | "
                         f"已花费: {cash_spent:.2f}/{TARGET_SPENT_CASH:.2f} | "
                         f"总持仓: {stock_held}")
        except Exception as e:
            logging.error(f"下单失败: {e}")
            time.sleep(1)

    logging.info(f">>> 吸筹阶段完成. 最终持仓: {stock_held} 股, 总花费: {cash_spent:.2f}")

    # 等待所有买单成交
    time.sleep(5)

    final_portfolio = get_portfolio(client)
    total_stock_to_sell = final_portfolio.get('stock_total', 0)
    if total_stock_to_sell == 0:
        logging.error("吸筹失败，未持有任何股票！")
        client.stop()
        return

    logging.info(f"确认最终待售股票数量: {total_stock_to_sell}")

    # --- 3. 拉高阶段 (Pump) ---
    logging.info(">>> 开始执行阶段二：发送新闻，拉高股价...")

    for i in range(10):
        try:
            client.send_truth(1.0)
            logging.info(f"第 {i+1}/10 次发送正面新闻成功！")
            time.sleep(0.2)  # 快速连续发送以形成冲击
        except Exception as e:
            logging.error(f"发送新闻失败: {e}")

    # --- 4. 出货阶段 (Distribution) ---
    logging.info(">>> 开始执行阶段三：高位挂单出货...")

    # 制定分层卖出策略
    sell_targets = [
        (0.25, baseline_price * 1.4),  # 卖出25%的仓位在基准价的1.4倍
        (0.25, baseline_price * 1.6),  # ... 1.6倍
        (0.25, baseline_price * 1.8),  # ... 1.8倍
        (0.25, baseline_price * 2.0)  # 剩余的在2.0倍或更高
    ]

    remaining_stock = total_stock_to_sell
    for ratio, price_target in sell_targets:
        qty_to_sell = int(total_stock_to_sell * ratio)
        if remaining_stock <= 0:
            break

        # 确保卖出所有股票
        if remaining_stock < qty_to_sell:
            qty_to_sell = remaining_stock

        try:
            client.submit_user_order(
                direction="sell",
                quantity=qty_to_sell,
                price=price_target
            )
            logging.info(f"挂出卖单: {qty_to_sell} 股 @ 目标价 {price_target:.2f}")
            remaining_stock -= qty_to_sell
        except Exception as e:
            logging.error(f"挂卖单失败: {e}")

    # 如果最后还有剩余的碎股，也挂单卖掉
    if remaining_stock > 0:
        price_target = baseline_price * 2.1
        client.submit_user_order("sell", remaining_stock, price_target)
        logging.info(f"挂出剩余卖单: {remaining_stock} 股 @ 目标价 {price_target:.2f}")

    logging.info("所有卖单已挂出，等待市场成交...")

    # --- 5. 监控与收尾 ---
    while True:
        current_tick, _ = get_current_tick_and_price(client)
        if current_tick is None or current_tick > 8950:
            break

        portfolio = get_portfolio(client)
        stock_left = portfolio.get('stock_total', 0)
        cash_total = portfolio.get('cash_total', 0)

        logging.info(f"[Tick {current_tick}] 监控: 剩余股票 {stock_left}, "
                     f"当前现金 {cash_total:,.2f}")

        if stock_left == 0:
            logging.info("所有股票已成功卖出！")
            break

        time.sleep(5)

    # 在模拟结束前，如果还有股票没卖掉，则市价清仓
    final_portfolio = get_portfolio(client)
    if final_portfolio.get('stock_total', 0) > 0:
        logging.warning("模拟即将结束，仍有持仓，市价清仓！")
        _, last_price = get_current_tick_and_price(client)
        if last_price:
            client.submit_user_order(
                direction="sell",
                quantity=final_portfolio['stock_total'],
                price=last_price * 0.9  # 以较低价格确保快速成交
            )

    time.sleep(2)  # 等待最后的清仓交易

    final_cash = get_portfolio(client).get('cash_total', 0)
    logging.info(f"策略执行完毕，最终现金: {final_cash:,.2f}")
    profit_rate = (final_cash - INITIAL_CASH) / INITIAL_CASH * 100
    logging.info(f"最终收益率: {profit_rate:.2f}%")

    # --- 6. 获取 Flag ---
    logging.info("尝试获取 Flag...")
    try:
        flag_response = client._get("/user/getflag")
        logging.info(f"Flag 1 (20% -> 6.0M): {flag_response.get('flag1')}")
        logging.info(f"Flag 2 (50% -> 7.5M): {flag_response.get('flag2')}")
        logging.info(f"Flag 3 (80% -> 9.0M): {flag_response.get('flag3')}")
    except Exception as e:
        logging.error(f"获取 Flag 失败: {e}")

    client.stop()
    logging.info("客户端已停止。")


if __name__ == "__main__":
    main()
