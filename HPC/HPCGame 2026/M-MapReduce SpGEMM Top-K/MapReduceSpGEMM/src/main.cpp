#include <mpi.h>

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "spgemm_topk.h"

static bool parse_triplet_line(const std::string& line, Triplet& t) {
	size_t p = 0;
	while (p < line.size() && std::isspace(static_cast<unsigned char>(line[p]))) p++;
	if (p == line.size() || line[p] == '#') return false;

	std::istringstream iss(line);
	if (!(iss >> t.r >> t.c >> t.v)) return false;
	return true;
}

static std::vector<std::string> collect_paths(const std::string& path) {
	namespace fs = std::filesystem;
	std::vector<std::string> paths;
	if (fs::is_directory(path)) {
		for (auto& p : fs::directory_iterator(path)) {
			if (!p.is_regular_file()) continue;
			paths.push_back(p.path().string());
		}
		std::sort(paths.begin(), paths.end());
	} else {
		paths.push_back(path);
	}
	return paths;
}

static std::vector<std::string> select_paths_round_robin(const std::vector<std::string>& paths,
												 int rank, int size) {
	std::vector<std::string> local;
	local.reserve((paths.size() + size - 1) / size);
	for (size_t i = 0; i < paths.size(); i++) {
		if (static_cast<int>(i % size) == rank) local.push_back(paths[i]);
	}
	return local;
}

// Each rank reads only its assigned input shards.
static std::vector<Triplet> read_coo_files(const std::vector<std::string>& paths) {
	std::vector<Triplet> out;
	for (const auto& path : paths) {
		std::ifstream fin(path);
		if (!fin) {
			std::cerr << "Failed to open file: " << path << "\n";
			MPI_Abort(MPI_COMM_WORLD, 1);
		}
		std::string line;
		while (std::getline(fin, line)) {
			Triplet t{};
			if (parse_triplet_line(line, t)) out.push_back(t);
		}
	}
	return out;
}

int main(int argc, char** argv) {
	MPI_Init(&argc, &argv);

	int rank = 0, size = 1;
	MPI_Comm_rank(MPI_COMM_WORLD, &rank);
	MPI_Comm_size(MPI_COMM_WORLD, &size);

	std::string pathA, pathB, outPath;
	int topK = 10;

	for (int i = 1; i < argc; i++) {
		std::string a = argv[i];
		auto need = [&](const char* name) {
			if (i + 1 >= argc) {
				if (rank == 0) std::cerr << "Missing value for " << name << "\n";
				MPI_Abort(MPI_COMM_WORLD, 2);
			}
			return std::string(argv[++i]);
		};
		if (a == "--A")
			pathA = need("--A");
		else if (a == "--B")
			pathB = need("--B");
		else if (a == "--topk")
			topK = std::stoi(need("--topk"));
		else if (a == "--out")
			outPath = need("--out");
		else if (a == "--help") {
			if (rank == 0) {
				std::cout << "Usage: mpirun -np P ./mr_spgemm_topk --A data/A --B data/B --topk 10 "
							 "[--out out.txt]\n";
			}
			MPI_Finalize();
			return 0;
		}
	}

	if (pathA.empty() || pathB.empty()) {
		if (rank == 0) std::cerr << "Need --A and --B\n";
		MPI_Abort(MPI_COMM_WORLD, 3);
	}

	auto pathsA = collect_paths(pathA);
	auto pathsB = collect_paths(pathB);
	auto local_pathsA = select_paths_round_robin(pathsA, rank, size);
	auto local_pathsB = select_paths_round_robin(pathsB, rank, size);

	double t0 = MPI_Wtime();

	auto A_local_read = read_coo_files(local_pathsA);	 // (i,k,val)
	auto B_local_read = read_coo_files(local_pathsB);	 // (k,j,val)

	double t_read = MPI_Wtime();
	auto result = spgemm_topk(A_local_read, B_local_read, topK, MPI_COMM_WORLD);
	std::string local_txt = result.local_txt;

	int local_len = static_cast<int>(local_txt.size());
	std::vector<int> recv_lens(size, 0);
	MPI_Gather(&local_len, 1, MPI_INT, recv_lens.data(), 1, MPI_INT, 0, MPI_COMM_WORLD);

	std::vector<int> displs;
	std::vector<char> allbuf;
	int total_len = 0;
	if (rank == 0) {
		displs.resize(size, 0);
		for (int r = 0; r < size; r++) {
			displs[r] = total_len;
			total_len += recv_lens[r];
		}
		allbuf.resize(total_len);
	}

	MPI_Gatherv(local_txt.data(), local_len, MPI_CHAR, rank == 0 ? allbuf.data() : nullptr,
				rank == 0 ? recv_lens.data() : nullptr, rank == 0 ? displs.data() : nullptr,
				MPI_CHAR, 0, MPI_COMM_WORLD);

	double t_end = MPI_Wtime();

	if (rank == 0) {
		std::string merged(allbuf.begin(), allbuf.end());
		if (!outPath.empty()) {
			std::ofstream fout(outPath);
			fout << merged;
		} else {
			std::cout << merged;
		}

		std::cerr << "Timing (s): read=" << (t_read - t0) << " shuffle=" << result.t_shuffle
				  << " compute=" << result.t_compute << " row_reduce=" << result.t_row_reduce
				  << " total=" << (t_end - t0) << "\n";
	}

	MPI_Finalize();
	return 0;
}
