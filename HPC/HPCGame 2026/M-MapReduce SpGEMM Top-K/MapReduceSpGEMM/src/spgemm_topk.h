#pragma once

#include <mpi.h>

#include <string>
#include <vector>

struct Triplet {
	int r;
	int c;
	double v;
};

struct ComputeResult {
	std::string local_txt;
	double t_shuffle = 0.0;
	double t_compute = 0.0;
	double t_row_reduce = 0.0;
};

// Contestants may edit only the implementation in spgemm_topk.cpp, not this signature.
ComputeResult spgemm_topk(const std::vector<Triplet>& A_local, const std::vector<Triplet>& B_local,
						  int topK, MPI_Comm comm);
