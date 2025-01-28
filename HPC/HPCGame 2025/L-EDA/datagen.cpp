#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <cassert>
#include <vector>

int main(int argc, const char **argv) {
  if(argc != 3) {
    printf("usage: %s <seed> <input.bin>\n", argv[0]);
    return 255;
  }
  srand(atoi(argv[1]));
  int num_nets = 1000000;
  std::vector<int> net_begin(1, 0);
  std::vector<int> xs, ys;
  for(int T = 0; T < num_nets; ++T) {
    int d = pow(rand() % 10000000 / 10000000. * 10 + 1.5, 2);
    net_begin.push_back(*net_begin.rbegin() + d);
    for(int i = 0; i < d; ++i) xs.push_back(rand() % 10000000);
    for(int i = 0; i < d; ++i) ys.push_back(rand() % 10000000);
  }
  FILE *fp = fopen(argv[2], "wb");
  assert(fp);
  fwrite(&num_nets, sizeof(int), 1, fp);
  fwrite(net_begin.data(), sizeof(int), net_begin.size(), fp);
  fwrite(xs.data(), sizeof(int), xs.size(), fp);
  fwrite(ys.data(), sizeof(int), ys.size(), fp);
  fclose(fp);
  return 0;
}