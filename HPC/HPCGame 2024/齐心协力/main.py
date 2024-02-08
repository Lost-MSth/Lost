import os
import ray
import numpy as np
#import time
#import logging

from ray.util.placement_group import (
    placement_group,
    placement_group_table,
    PlacementGroupSchedulingStrategy,
)

#logging.basicConfig(level=logging.INFO)
#ray.init()
ray.init(address=f"{os.environ['RAY_CLUSTER_ADDR']}")

CPU_NUM = 4

#logging.info("Init placement group...")
pg = placement_group([{"CPU": CPU_NUM} for _ in range(4)], strategy="PACK")

ray.get(pg.ready(), timeout=10)
#logging.info(placement_group_table(pg))


@ray.remote(num_cpus=CPU_NUM)
def run_A(i, A):
    #m = np.random.rand(10, 10)
    #time.sleep(1)
    m = np.load(f"inputs/input_{i}.npy")
    #A = np.load("weights/weight_0.npy")
    A = ray.get(A)
    m = m @ A
    m = np.maximum(m, 0)
    return ray.put(m)
    
@ray.remote(num_cpus=CPU_NUM)
def run_B(m, B):
    m = ray.get(m)
    #B = np.load("weights/weight_1.npy")
    B = ray.get(B)
    m = m @ B
    #time.sleep(1)
    m = np.maximum(m, 0)
    return ray.put(m)

@ray.remote(num_cpus=CPU_NUM)
def run_C(m, C):
    m = ray.get(m)
    #C = np.load("weights/weight_2.npy")
    C = ray.get(C)
    m = m @ C
    #time.sleep(1)
    m = np.maximum(m, 0)
    return ray.put(m)

@ray.remote(num_cpus=CPU_NUM)
def run_D(i, m, D):
    m = ray.get(m)
    #D = np.load("weights/weight_3.npy")
    D = ray.get(D)
    m = m @ D
    #time.sleep(1)
    m = np.maximum(m, 0)

    np.save(f"outputs/output_{i}.npy", m)
    return

@ray.remote(num_cpus=CPU_NUM)
def load_weight(i):
    #return ray.put(np.random.rand(10, 10))
    return ray.put(np.load(f"weights/weight_{i}.npy"))

#@ray.remote
def pipe_run(i, A, B, C, D):
    m = run_A.options(scheduling_strategy=PlacementGroupSchedulingStrategy(
        placement_group=pg,
        placement_group_bundle_index=0,
    )).remote(i, A)
    m = run_B.options(scheduling_strategy=PlacementGroupSchedulingStrategy(
        placement_group=pg,
        placement_group_bundle_index=1,
    )).remote(m, B)
    m = run_C.options(scheduling_strategy=PlacementGroupSchedulingStrategy(
        placement_group=pg,
        placement_group_bundle_index=2,
    )).remote(m, C)
    x = run_D.options(scheduling_strategy=PlacementGroupSchedulingStrategy(
        placement_group=pg,
        placement_group_bundle_index=3,
    )).remote(i, m, D)
    return x


def main():
    # 检测并建立 outputs 文件夹
    #logging.info("Init...")
    if not os.path.exists("outputs"):
        os.mkdir("outputs")
    A = load_weight.options(scheduling_strategy=PlacementGroupSchedulingStrategy(
        placement_group=pg,
        placement_group_bundle_index=0,
    )).remote(0)
    B = load_weight.options(scheduling_strategy=PlacementGroupSchedulingStrategy(
        placement_group=pg,
        placement_group_bundle_index=1,
    )).remote(1)
    C = load_weight.options(scheduling_strategy=PlacementGroupSchedulingStrategy(
        placement_group=pg,
        placement_group_bundle_index=2,
    )).remote(2)
    D = load_weight.options(scheduling_strategy=PlacementGroupSchedulingStrategy(
        placement_group=pg,
        placement_group_bundle_index=3,
    )).remote(3)
    #logging.info("Start...")

    x = [pipe_run(i, A, B, C, D) for i in range(100)]
    ray.get(x)
        # t = time()
        # ray.get(i)
        # logging.info(f"{i} {time() - t}")
    
    #logging.info("Done!")



if __name__ == "__main__":
    main()
    #ray.get(main.remote())