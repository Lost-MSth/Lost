import Pkg
Pkg.activate(temp=true)
Pkg.add("DataStructures")

using DataStructures

function Nlargest(v,N)
    maxn = heapify!(tuple.(v[1:N], 1:N))
    maxn1 = maxn[1]
    for i in N+1:length(v)
        e = (v[i], i)    
        if maxn1[1] < e[1]
            heappop!(maxn)
            heappush!(maxn, e)
            maxn1 = maxn[1]
        end
    end
    sort!(maxn, rev=true)
    # maxn
    # get only idx
    return [x[2] for x in maxn]
end


using Base.Threads

# 原子类型定义，用于线程安全的操作
mutable struct Atomic{T}
    @atomic x::T
end


@inbounds function topk(data::AbstractVector{T}, k) where T
    
    # maxn = Nlargest(data, k)
    # return maxn

    n = length(data)
    chunk_size = ceil(Int, n / nthreads())
    results = Vector{Vector{Int}}(undef, nthreads())

    @threads for i in 1:nthreads()
        start_idx = (i - 1) * chunk_size + 1
        end_idx = min(i * chunk_size, n)
        results[i] = Nlargest(data[start_idx:end_idx], k) .+ (start_idx - 1)
        # results[i] = partialsortperm(data[start_idx:end_idx], 1:k, rev=true) .+ (start_idx - 1)
    end

    combined_indices = vcat(results...)
    # final_indices = partialsortperm(data[combined_indices], 1:k, rev=true)
    final_indices = Nlargest(data[combined_indices], k)
    return combined_indices[final_indices]
end

# @inbounds function topk(data::AbstractVector{Int64}, k)

#     n = length(data)
#     chunk_size = ceil(Int, n / nthreads())
#     results = Vector{Vector{Int}}(undef, nthreads())

#     @threads for i in 1:nthreads()
#         start_idx = (i - 1) * chunk_size + 1
#         end_idx = min(i * chunk_size, n)
        
#         # radix sort top k
#         part_data = data[start_idx:end_idx]
#         idx_buckets = Vector{Vector{Int}}(undef, 256)
#         for j in 1:256
#             idx_buckets[j] = Vector{Int}()
#         end
#         for j in 1:length(part_data)
#             idx = part_data[j] >> 56 & 0xff
#             # 忽略负数
#             if idx > 128
#                 continue
#             end
#             push!(idx_buckets[idx + 1], j)
#         end

#         selected = Vector{Int}()
#         for j in 128:-1:1
#             selected = vcat(selected, idx_buckets[j])
#             if length(selected) >= k
#                 break
#             end
#         end
#         # 偷个懒，直接忽略负数

#         results[i] = selected .+ (start_idx - 1)
#     end
    

#     combined_indices = vcat(results...)
#     final_indices = partialsortperm(data[combined_indices], 1:k, rev=true)
#     return combined_indices[final_indices]
# end

# @inbounds function topk(data::AbstractVector{Float64}, k)
#     n = length(data)
#     chunk_size = ceil(Int, n / nthreads())
#     results = Vector{Vector{Int}}(undef, nthreads())

#     @threads for i in 1:nthreads()
#         start_idx = (i - 1) * chunk_size + 1
#         end_idx = min(i * chunk_size, n)
#         results[i] = partialsortperm(data[start_idx:end_idx], 1:k, rev=true) .+ (start_idx - 1)
#     end

#     combined_indices = vcat(results...)
#     final_indices = partialsortperm(data[combined_indices], 1:k, rev=true)
#     return combined_indices[final_indices]
# end
