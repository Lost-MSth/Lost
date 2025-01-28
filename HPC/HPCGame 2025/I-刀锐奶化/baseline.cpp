#include <math.h>
#include <stdio.h>
#include <malloc.h>
#include <stdint.h>

typedef double d_t;
struct d3_t {
    d_t x, y, z;
};

d_t norm(d3_t x) {
    return sqrt(x.x * x.x + x.y * x.y + x.z * x.z);
}

d3_t operator-(d3_t a, d3_t b) {
    return {a.x-b.x,a.y-b.y,a.z-b.z};
}

int main(){
    FILE* fi;
    fi = fopen("in.data", "rb");
    d3_t src;
    int64_t mirn,senn;
    d3_t* mir, * sen;

    fread(&src, 1, sizeof(d3_t), fi);
    
    fread(&mirn, 1, sizeof(int64_t), fi);
    mir = (d3_t*)malloc(mirn * sizeof(d3_t));
    fread(mir, 1, mirn * sizeof(d3_t), fi);

    fread(&senn, 1, sizeof(int64_t), fi);
    sen = (d3_t*)malloc(senn * sizeof(d3_t));
    fread(sen, 1, senn * sizeof(d3_t), fi);

    fclose(fi);

    d_t* data = (d_t*)malloc(senn * sizeof(d_t));

    for (int64_t i = 0; i < senn; i++) {
        d_t a=0;
        d_t b=0;
        for (int64_t j = 0; j < mirn; j++) {
            d_t l = norm(mir[j] - src) + norm(mir[j] - sen[i]);
            a += cos(6.283185307179586 * 2000 * l);
            b += sin(6.283185307179586 * 2000 * l);
        }
        data[i] = sqrt(a * a + b * b);
    }

    fi = fopen("out.data", "wb");
    fwrite(data, 1, senn * sizeof(d_t), fi);
    fclose(fi);

    return 0;
}