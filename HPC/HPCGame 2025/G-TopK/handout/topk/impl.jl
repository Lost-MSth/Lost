# 原子类型定义，用于线程安全的操作
mutable struct Atomic{T}; @atomic x::T; end

@inbounds function topk(data::AbstractVector{T}, k) where T
    return ans
end
