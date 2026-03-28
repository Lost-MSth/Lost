#include "spgemm_topk.h"

#include <algorithm>
#include <cstring>
#include <sstream>
#include <unordered_map>
#include <utility>
#include <vector>

static void pack_triplets(const std::vector<Triplet>& vec, std::vector<char>& buf) {
  buf.resize(vec.size() * sizeof(Triplet));
  if (!vec.empty()) std::memcpy(buf.data(), vec.data(), buf.size());
}

static std::vector<Triplet> unpack_triplets(const std::vector<char>& buf) {
  std::vector<Triplet> vec(buf.size() / sizeof(Triplet));
  if (!buf.empty()) std::memcpy(vec.data(), buf.data(), buf.size());
  return vec;
}

static std::vector<std::pair<int, double>> topk_from_map(const std::unordered_map<int, double>& m, int K) {
  std::vector<std::pair<int, double>> v;
  v.reserve(m.size());
  for (auto& kv : m) v.push_back(kv);
  if (static_cast<int>(v.size()) <= K) {
    std::sort(v.begin(), v.end(), [](auto& a, auto& b) { return a.second > b.second; });
    return v;
  }
  std::nth_element(v.begin(), v.begin() + K, v.end(), [](auto& a, auto& b) { return a.second > b.second; });
  v.resize(K);
  std::sort(v.begin(), v.end(), [](auto& a, auto& b) { return a.second > b.second; });
  return v;
}

// Naive: allgather full A and B to every rank, compute locally. Only suitable for small cases.
ComputeResult spgemm_topk(const std::vector<Triplet>& A_local,
                          const std::vector<Triplet>& B_local,
                          int topK,
                          MPI_Comm comm) {
  int rank = 0, size = 1;
  MPI_Comm_rank(comm, &rank);
  MPI_Comm_size(comm, &size);

  double t0 = MPI_Wtime();

  // Serialize locals
  std::vector<char> sendA, sendB;
  pack_triplets(A_local, sendA);
  pack_triplets(B_local, sendB);

  int sendA_bytes = static_cast<int>(sendA.size());
  int sendB_bytes = static_cast<int>(sendB.size());
  std::vector<int> recvA_bytes(size, 0), recvB_bytes(size, 0);
  MPI_Allgather(&sendA_bytes, 1, MPI_INT, recvA_bytes.data(), 1, MPI_INT, comm);
  MPI_Allgather(&sendB_bytes, 1, MPI_INT, recvB_bytes.data(), 1, MPI_INT, comm);

  auto prefix = [](const std::vector<int>& v) {
    std::vector<int> p(v.size(), 0);
    int s = 0;
    for (size_t i = 0; i < v.size(); i++) {
      p[i] = s;
      s += v[i];
    }
    return p;
  };
  std::vector<int> dispA = prefix(recvA_bytes), dispB = prefix(recvB_bytes);
  int totalA = dispA.back() + recvA_bytes.back();
  int totalB = dispB.back() + recvB_bytes.back();
  std::vector<char> allA(totalA), allB(totalB);

  MPI_Allgatherv(sendA.data(), sendA_bytes, MPI_CHAR,
                 allA.data(), recvA_bytes.data(), dispA.data(), MPI_CHAR,
                 comm);
  MPI_Allgatherv(sendB.data(), sendB_bytes, MPI_CHAR,
                 allB.data(), recvB_bytes.data(), dispB.data(), MPI_CHAR,
                 comm);

  auto A_full = unpack_triplets(allA);
  auto B_full = unpack_triplets(allB);

  double t_shuffle = MPI_Wtime(); // here shuffle means gather

  std::unordered_map<int, std::vector<std::pair<int, double>>> B_by_k;
  B_by_k.reserve(B_full.size());
  for (const auto& t : B_full) {
    B_by_k[t.r].push_back({t.c, t.v});
  }

  std::unordered_map<int, std::unordered_map<int, double>> acc;
  acc.reserve(A_full.size());
  for (const auto& t : A_full) {
    int i = t.r;
    int k = t.c;
    double a = t.v;
    auto it = B_by_k.find(k);
    if (it == B_by_k.end()) continue;
    auto& row = acc[i];
    for (const auto& jb : it->second) {
      row[jb.first] += a * jb.second;
    }
  }

  double t_compute = MPI_Wtime();

  std::ostringstream oss;
  for (auto& ikv : acc) {
    auto top = topk_from_map(ikv.second, topK);
    oss << ikv.first;
    for (auto& js : top) {
      oss << " " << js.first << ":" << js.second;
    }
    oss << "\n";
  }

  double t_row_reduce = MPI_Wtime();

  ComputeResult res;
  res.local_txt = oss.str();
  res.t_shuffle = t_shuffle - t0;
  res.t_compute = t_compute - t_shuffle;
  res.t_row_reduce = t_row_reduce - t_compute;
  return res;
}
