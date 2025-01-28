using Random
Random.seed!(42)

include("impl.jl")

# Warmup
topk(rand(Int64, 1 << 20), 1 << 8)
topk(randn(Float64, 1 << 20), 1 << 8)

i64_1m = rand(Int64, 1 << 20)
f64_1m = randn(Float64, 1 << 20)

# 1M
println("Testing on 1M data...")
res, time_i64_1m = @timed topk(i64_1m, 1 << 8)
ref, time_i64_1m_base = @timed partialsortperm(i64_1m, 1:1 << 8, rev=true)
@assert all(res .== ref) "Failed for Int64 1M"

res, time_f64_1m = @timed topk(f64_1m, 1 << 8)
ref, time_f64_1m_base = @timed partialsortperm(f64_1m, 1:1 << 8, rev=true)
@assert all(res .== ref) "Failed for Float64 1M"

println("Base: ", [time_i64_1m_base, time_f64_1m_base])
println("Impl: ", [time_i64_1m, time_f64_1m])
println("Speedup: ", [time_i64_1m_base / time_i64_1m, time_f64_1m_base / time_f64_1m])

# # 1B
# i64_1b = rand(Int64, 1 << 30)
# f64_1b = randn(Float64, 1 << 30)

# println("Testing on 1B data...")
# res, time_i64_1b = @timed topk(i64_1b, 1 << 10)
# ref, time_i64_1b_base = @timed partialsortperm(i64_1b, 1:1 << 10, rev=true)
# @assert all(res .== ref) "Failed for Int64 1B"

# res, time_f64_1b = @timed topk(f64_1b, 1 << 10)
# ref, time_f64_1b_base = @timed partialsortperm(f64_1b, 1:1 << 10, rev=true)
# @assert all(res .== ref) "Failed for Float64 1B"

# println("Base: ", [time_i64_1b_base, time_f64_1b_base])
# println("Impl: ", [time_i64_1b, time_f64_1b])
# println("Speedup: ", [time_i64_1b_base / time_i64_1b, time_f64_1b_base / time_f64_1b])
