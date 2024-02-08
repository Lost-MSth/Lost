#include <omp.h>

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iostream>
#include <tuple>
#include <vector>

using std::vector, std::array, std::tuple, std::string;

#define THREADS 7

#pragma omp declare reduction(vsum : std::vector<double> : std::transform( \
        omp_out.begin(), omp_out.end(), omp_in.begin(), omp_out.begin(),   \
            std::plus<double>()))                                          \
    initializer(omp_priv = decltype(omp_orig)(omp_orig.size()))

void particle2grid(int resolution, int numparticle,
                   const vector<double> &particle_position,
                   const vector<double> &particle_velocity,
                   vector<double> &velocityu, vector<double> &velocityv,
                   vector<double> &weightu, vector<double> &weightv) {
    double grid_spacing = 1.0 / resolution;
    double inv_grid_spacing = 1.0 / grid_spacing;
    auto get_frac = [&inv_grid_spacing](double x, double y) {
        int xidx = floor(x * inv_grid_spacing);
        int yidx = floor(y * inv_grid_spacing);
        double fracx = x * inv_grid_spacing - xidx;
        double fracy = y * inv_grid_spacing - yidx;
        return tuple(
            array<int, 2>{xidx, yidx},
            array<double, 4>{fracx * fracy, (1 - fracx) * fracy,
                             fracx * (1 - fracy), (1 - fracx) * (1 - fracy)});
    };

    array<int, 4> offsetx = {0, 1, 0, 1};
    array<int, 4> offsety = {0, 0, 1, 1};

#pragma omp parallel for reduction(vsum : velocityu, velocityv, weightu, \
                                       weightv) num_threads(THREADS)
    for (int i = 0; i < numparticle; i++) {
        auto [idxu, fracu] =
            get_frac(particle_position[i * 2 + 0],
                     particle_position[i * 2 + 1] - 0.5 * grid_spacing);
        auto [idxv, fracv] =
            get_frac(particle_position[i * 2 + 0] - 0.5 * grid_spacing,
                     particle_position[i * 2 + 1]);

        for (int j = 0; j < 4; j++) {
            int tmpidx = 0;
            tmpidx =
                (idxu[0] + offsetx[j]) * resolution + (idxu[1] + offsety[j]);
            velocityu[tmpidx] += particle_velocity[i * 2 + 0] * fracu[j];
            weightu[tmpidx] += fracu[j];

            tmpidx = (idxv[0] + offsetx[j]) * (resolution + 1) +
                     (idxv[1] + offsety[j]);

            velocityv[tmpidx] += particle_velocity[i * 2 + 1] * fracv[j];
            weightv[tmpidx] += fracv[j];
        }
    }
}
// void particle2grid(int resolution, int numparticle,
//                    const vector<double> &particle_position,
//                    const vector<double> &particle_velocity,
//                    vector<double> &velocityu, vector<double> &velocityv,
//                    vector<double> &weightu, vector<double> &weightv) {
//     double grid_spacing = 1.0 / resolution;
//     double inv_grid_spacing = 1.0 / grid_spacing;
//     auto get_frac = [&inv_grid_spacing](double x, double y) {
//         int xidx = floor(x * inv_grid_spacing);
//         int yidx = floor(y * inv_grid_spacing);
//         double fracx = x * inv_grid_spacing - xidx;
//         double fracy = y * inv_grid_spacing - yidx;
//         return tuple(
//             array<int, 2>{xidx, yidx},
//             array<double, 4>{fracx * fracy, (1 - fracx) * fracy,
//                              fracx * (1 - fracy), (1 - fracx) * (1 -
//                              fracy)});
//     };

//     array<int, 4> offsetx = {0, 1, 0, 1};
//     array<int, 4> offsety = {0, 0, 1, 1};

//     // double *velocityu_ptr = velocityu.data();
//     // double *velocityv_ptr = velocityv.data();
//     // double *weightu_ptr = weightu.data();
//     // double *weightv_ptr = weightv.data();

//     // #pragma omp parallel for reduction(+ : velocityu_ptr[ : velocityu.size()], \
//     //                                    velocityv_ptr[ : velocityv.size()], \
//     //                                    weightu_ptr[ : weightu.size()], \
//     //                                    weightv_ptr[ : weightv.size()])

//     int size = velocityu.size();
//     std::vector<double> vu[THREADS], vv[THREADS], wu[THREADS], wv[THREADS];

//     for (int i = 0; i < THREADS; i++) {
//         vu[i].resize(size, 0.0);
//         vv[i].resize(size, 0.0);
//         wu[i].resize(size, 0.0);
//         wv[i].resize(size, 0.0);
//     }

// #pragma omp parallel for num_threads(THREADS) shared(particle_position,
// particle_velocity, vu, vv, wu, wv, offsetx, offsety)
//     for (int i = 0; i < numparticle; i++) {
//         // printf("thread: %d\n", omp_get_thread_num());

//         auto [idxu, fracu] =
//             get_frac(particle_position[i * 2 + 0],
//                      particle_position[i * 2 + 1] - 0.5 * grid_spacing);
//         auto [idxv, fracv] =
//             get_frac(particle_position[i * 2 + 0] - 0.5 * grid_spacing,
//                      particle_position[i * 2 + 1]);

//         for (int j = 0; j < 4; j++) {
//             int tmpidx = 0;
//             tmpidx =
//                 (idxu[0] + offsetx[j]) * resolution + (idxu[1] + offsety[j]);

//             vu[omp_get_thread_num()][tmpidx] +=
//                 particle_velocity[i * 2 + 0] * fracu[j];
//             wu[omp_get_thread_num()][tmpidx] += fracu[j];
//             // velocityu_ptr[tmpidx] +=
//             //     particle_velocity[i * 2 + 0] * fracu[j];
//             // weightu_ptr[tmpidx] += fracu[j];

//             tmpidx = (idxv[0] + offsetx[j]) * (resolution + 1) +
//                      (idxv[1] + offsety[j]);

//             vv[omp_get_thread_num()][tmpidx] +=
//                 particle_velocity[i * 2 + 1] * fracv[j];
//             wv[omp_get_thread_num()][tmpidx] += fracv[j];

//             // velocityv_ptr[tmpidx] += particle_velocity[i * 2 + 1] *
//             fracv[j];
//             // weightv_ptr[tmpidx] += fracv[j];
//         }
//     }

// #pragma omp parallel for shared(velocityu, velocityv, weightu, weightv)
// collapse(2)
//     for (int i = 0; i < size; i++) {
//         for (int j = 0; j < THREADS; j++) {
//             velocityu[i] += vu[j][i];
//             velocityv[i] += vv[j][i];
//             weightu[i] += wu[j][i];
//             weightv[i] += wv[j][i];
//         }
//     }
// }

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s inputfile\n", argv[0]);
        return -1;
    }

    string inputfile(argv[1]);
    std::ifstream fin(inputfile, std::ios::binary);
    if (!fin) {
        printf("Error opening file");
        return -1;
    }

    int resolution;
    int numparticle;
    vector<double> particle_position;
    vector<double> particle_velocity;

    fin.read((char *)(&resolution), sizeof(int));
    fin.read((char *)(&numparticle), sizeof(int));

    particle_position.resize(numparticle * 2);
    particle_velocity.resize(numparticle * 2);

    // resolution = 2048;

    // printf("resolution: %d\n", resolution);
    // printf("numparticle: %d\n", numparticle);

    fin.read((char *)(particle_position.data()),
             sizeof(double) * particle_position.size());
    fin.read((char *)(particle_velocity.data()),
             sizeof(double) * particle_velocity.size());

    vector<double> velocityu((resolution + 1) * resolution, 0.0);
    vector<double> velocityv((resolution + 1) * resolution, 0.0);
    vector<double> weightu((resolution + 1) * resolution, 0.0);
    vector<double> weightv((resolution + 1) * resolution, 0.0);

    string outputfile;

    // auto start = std::chrono::high_resolution_clock::now();
    particle2grid(resolution, numparticle, particle_position, particle_velocity,
                  velocityu, velocityv, weightu, weightv);
    // auto end = std::chrono::high_resolution_clock::now();
    // printf("Time: %f\n",
    //        std::chrono::duration<double>(end - start).count() * 1000);
    outputfile = "output.dat";

    std::ofstream fout(outputfile, std::ios::binary);
    if (!fout) {
        printf("Error output file");
        return -1;
    }
    fout.write((char *)(&resolution), sizeof(int));
    fout.write(reinterpret_cast<char *>(velocityu.data()),
               sizeof(double) * velocityu.size());
    fout.write(reinterpret_cast<char *>(velocityv.data()),
               sizeof(double) * velocityv.size());
    fout.write(reinterpret_cast<char *>(weightu.data()),
               sizeof(double) * weightu.size());
    fout.write(reinterpret_cast<char *>(weightv.data()),
               sizeof(double) * weightv.size());

    return 0;
}