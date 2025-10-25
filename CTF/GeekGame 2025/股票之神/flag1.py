# solve_final_v2.py
import time
import sys
from python_sdk import SimulationClient


def get_latest_price(client: SimulationClient):
    """Safely gets the most recent price from the client's state."""
    return client.state.last_price or 100.0


def cancel_all_open_orders(client: SimulationClient):
    """Crucial for ensuring a clean slate before each strategic phase."""
    try:
        orders_info = client.list_user_orders()
        open_orders = orders_info.get('open_orders', [])
        if open_orders:
            print("🧹 Cleaning slate: Cancelling outstanding orders...")
            for order in open_orders:
                client.cancel_user_order(order['order_id'])
            # A brief pause is good practice to allow the exchange to process cancellations.
            time.sleep(0.2)
    except Exception as e:
        print(f"  - Warning: Could not cancel orders: {e}", file=sys.stderr)


def solve():
    # 请根据题目实际地址修改
    client = SimulationClient(base_url="http://127.0.0.1:8080")

    print("🚀 Connecting to simulation server...")
    client.start()
    if not client.wait_until_connected(timeout=10):
        print("❌ Connection failed.", file=sys.stderr)
        client.stop()
        return

    try:
        print("📈 Starting simulation and setting max speed...")
        client.start_simulation()
        client.set_tick_duration(0.02)
        # Wait for the first tick to ensure the simulation is live and state is populated.
        client.get_event(timeout=10)

        for i in range(1, 6):  # Give it up to 5 cycles, though 2-3 should be enough
            print(f"\n{'='*15} Cycle {i}/5: The Final Strategy {'='*15}")

            cancel_all_open_orders(client)

            # --- PHASE 1: DUMP & AGGRESSIVE BUY ---
            print("Phase 1: Creating panic and setting a deep buy trap.")
            price = get_latest_price(client)
            client.refresh_user_orders()
            cash = client.state.portfolio.get('cash_available', 0)

            # We want to be a giant sponge, absorbing all panic selling.
            buy_price1 = round(price * 0.95, 2)
            buy_price2 = round(price * 0.92, 2)
            qty1 = int((cash * 0.5) / buy_price1) if buy_price1 > 0 else 0
            qty2 = int((cash * 0.5) / buy_price2) if buy_price2 > 0 else 0

            # This is the core timing: send truth, then IMMEDIATELY send orders.
            # They will be processed in the next tick BEFORE retail orders.
            client.send_truth(-1.0)
            if qty1 > 0:
                client.submit_user_order("buy", qty1, buy_price1)
            if qty2 > 0:
                client.submit_user_order("buy", qty2, buy_price2)
            print(
                f"  - TRAP SET: Buying {qty1} @ ${buy_price1} and {qty2} @ ${buy_price2}")

            # Wait for the tick to process and our local state to reflect the purchase.
            time.sleep(10)

            # --- PHASE 2: PUMP & LAYERED SELL-OFF ---
            # Clean up any tiny, unfilled buy orders. CRITICAL for freeing up assets.
            cancel_all_open_orders(client)

            price = get_latest_price(client)  # Price is now at rock bottom.
            client.refresh_user_orders()
            stock = client.state.portfolio.get('stock_available', 0)

            if stock < 100:
                print("  - ⚠️ Buy trap missed. Not enough stock caught. Retrying cycle.")
                continue

            print(
                f"Phase 2: Acquired {stock} shares. Initiating multi-layered distribution.")

            # The "Smart Money" sell-off strategy. We are the house now.
            # We create a sell wall at different prices to ensure we sell EVERYTHING.
            sell_prices = [
                round(price * 1.03, 2), 
                # round(price * 1.02, 2),
                round(price * 0.95, 2),
            ]

            # Once again, the core timing trick.
            client.send_truth(1.0)
            for p, sleep_time in zip(sell_prices, [1.0, 2.0]):
                if stock > 0:
                    client.submit_user_order("sell", stock, p)
                    print(f"  - SELL ORDER: Selling {stock} @ ${p}")
                    time.sleep(sleep_time)  # Stagger orders slightly
                    # Cancel to avoid partial fills.
                    cancel_all_open_orders(client)
                stock = client.state.portfolio.get('stock_available', 0)

            time.sleep(1.0)

            # --- PHASE 3: REVIEW & REPEAT ---
            client.refresh_user_orders()
            final_cash = client.state.portfolio.get('cash_total', 0)
            final_stock = client.state.portfolio.get('stock_total', 0)
            print(
                f"💰 Cycle Complete! Final Cash: ${final_cash:,.2f}, Stock Left: {final_stock}")

            # print("\n🏁 Checking for flags...")
            # flags = client.get_flag()
            # print(f"  - Flag 1 (6.0M): {flags.get('flag1', '...')}")
            # print(f"  - Flag 2 (7.5M): {flags.get('flag2', '...')}")
            # print(f"  - Flag 3 (9.0M): {flags.get('flag3', '...')}")

            # if "flag{" in flags.get('flag3', ''):
            #     print("\n🎉🎉🎉 CHECKMATE! All flags captured. The market is ours. 🎉🎉🎉")
            #     break

    except (Exception, KeyboardInterrupt) as e:
        print(f"\n❌ An unexpected error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        print("🛑 Shutting down client.")
        client.stop()


if __name__ == "__main__":
    solve()
