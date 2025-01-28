#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

#include <algorithm>
#include <cassert>
using std::max;
using std::min;

typedef unsigned DTYPE;

typedef struct {
    DTYPE x, y;  // starting point of the branch
    int n;       // index of neighbor
} Branch;

typedef struct {
    int deg;         // degree
    DTYPE length;    // total wirelength
    Branch *branch;  // array of tree branches
} Tree;

// Major functions
void readLUT();
DTYPE flute_wl(int d, DTYPE x[], DTYPE y[], int acc);
// Macro: DTYPE flutes_wl(int d, DTYPE xs[], DTYPE ys[], int s[], int acc);
Tree flute(int d, DTYPE x[], DTYPE y[], int acc);
// Macro: Tree flutes(int d, DTYPE xs[], DTYPE ys[], int s[], int acc);
DTYPE wirelength(Tree t);
void printtree(Tree t);

#define POWVFILE "POWV9.dat"    // LUT for POWV (Wirelength Vector)
#define PORTFILE "PORT9.dat"    // LUT for PORT (Routing Tree)
#define D 9                     // LUT is used for d <= D, D <= 9
#define FLUTEROUTING 1          // 1 to construct routing, 0 to estimate WL only
#define REMOVE_DUPLICATE_PIN 0  // Remove dup. pin for flute_wl() & flute()
#define ACCURACY 8              // Default accuracy is 8
// #define MAXD 2008840  // max. degree of a net that can be handled
#define MAXD 1000  // max. degree of a net that can be handled

// Other useful functions
DTYPE flutes_wl_LD(int d, DTYPE xs[], DTYPE ys[], int s[]);
DTYPE flutes_wl_MD(int d, DTYPE xs[], DTYPE ys[], int s[], int acc);
DTYPE flutes_wl_RDP(int d, DTYPE xs[], DTYPE ys[], int s[], int acc);
Tree flutes_LD(int d, DTYPE xs[], DTYPE ys[], int s[]);
Tree flutes_MD(int d, DTYPE xs[], DTYPE ys[], int s[], int acc);
Tree flutes_RDP(int d, DTYPE xs[], DTYPE ys[], int s[], int acc);

#if REMOVE_DUPLICATE_PIN == 1
    #define flutes_wl(d, xs, ys, s, acc) flutes_wl_RDP(d, xs, ys, s, acc)
    #define flutes(d, xs, ys, s, acc) flutes_RDP(d, xs, ys, s, acc)
#else
    #define flutes_wl(d, xs, ys, s, acc) flutes_wl_ALLD(d, xs, ys, s, acc)
    #define flutes(d, xs, ys, s, acc) flutes_ALLD(d, xs, ys, s, acc)
#endif

#define flutes_wl_ALLD(d, xs, ys, s, acc) flutes_wl_LMD(d, xs, ys, s, acc)
#define flutes_ALLD(d, xs, ys, s, acc) flutes_LMD(d, xs, ys, s, acc)

#define flutes_wl_LMD(d, xs, ys, s, acc) \
    (d <= D ? flutes_wl_LD(d, xs, ys, s) : flutes_wl_MD(d, xs, ys, s, acc))
#define flutes_LMD(d, xs, ys, s, acc) \
    (d <= D ? flutes_LD(d, xs, ys, s) : flutes_MD(d, xs, ys, s, acc))

#define ADIFF(x, y) ((x) > (y) ? (x - y) : (y - x))  // Absolute difference

#if D <= 7
    #define MGROUP 5040 / 4  // Max. # of groups, 7! = 5040
    #define MPOWV 15         // Max. # of POWVs per group
#elif D == 8
    #define MGROUP 40320 / 4  // Max. # of groups, 8! = 40320
    #define MPOWV 33          // Max. # of POWVs per group
#elif D == 9
    #define MGROUP 362880 / 4  // Max. # of groups, 9! = 362880
    #define MPOWV 79           // Max. # of POWVs per group
#endif
int numgrp[10] = {0, 0, 0, 0, 6, 30, 180, 1260, 10080, 90720};

typedef struct point {
    DTYPE x, y;
    int o;  // ZZ: temporarily store discretized x value indices
} POINT;

typedef POINT *POINTptr;

struct csoln {
    unsigned char parent;
    unsigned char seg[12];  // Add: 0..i, Sub: j..11; seg[i+1]=seg[j-1]=0
    unsigned char row[D - 2], col[D - 2];
    unsigned char neighbor[2 * D - 2];
};

struct csoln *LUT[D + 1][MGROUP];  // storing 4 .. D
int numsoln[D + 1][MGROUP];

void readLUT();
Tree flute(int d, DTYPE x[], DTYPE y[], int acc);
Tree flutes_LD(int d, DTYPE xs[], DTYPE ys[], int s[]);
Tree flutes_MD(int d, DTYPE xs[], DTYPE ys[], int s[], int acc);
Tree flutes_RDP(int d, DTYPE xs[], DTYPE ys[], int s[], int acc);
Tree dmergetree(Tree t1, Tree t2);
Tree hmergetree(Tree t1, Tree t2, int s[]);
Tree vmergetree(Tree t1, Tree t2);
void printtree(Tree t);

void readLUT() {
    static bool LUTread = false;
    if (LUTread) return;
    LUTread = true;

    FILE *fpwv, *fprt;
    struct csoln *p;
    int d, i, j, k, kk, ns, nn, ne;
    unsigned char line[99], *linep, c;
    unsigned char charnum[256];
    unsigned char divd[256], modd[256], div16[256], mod16[256], dsq;

    for (i = 0; i <= 255; i++) {
        if ('0' <= i && i <= '9')
            charnum[i] = i - '0';
        else if (i >= 'A')
            charnum[i] = i - 'A' + 10;
        else  // if (i=='$' || i=='\n' || ... )
            charnum[i] = 0;

        div16[i] = i / 16;
        mod16[i] = i % 16;
    }

    fpwv = fopen(POWVFILE, "r");
    if (fpwv == NULL) {
        printf("Error in opening %s\n", POWVFILE);
        printf(
            "Please make sure %s and %s\n"
            "are in the current working directory.\n",
            POWVFILE, PORTFILE);
        exit(1);
    }

#if FLUTEROUTING == 1
    fprt = fopen(PORTFILE, "r");
    if (fprt == NULL) {
        printf("Error in opening %s\n", PORTFILE);
        printf(
            "Please make sure %s and %s\n(found in the Flute directory of "
            "UMpack)\n"
            "are in the current working directory.\n",
            POWVFILE, PORTFILE);
        exit(1);
    }
#endif

    for (d = 4; d <= D; d++) {
        for (i = 0; i <= 255; i++) {
            divd[i] = i / d;
            modd[i] = i % d;
        }
        dsq = d * d;

        fscanf(fpwv, "d=%d\n", &d);
#if FLUTEROUTING == 1
        fscanf(fprt, "d=%d\n", &d);
#endif
        for (k = 0; k < numgrp[d]; k++) {
            ns = (int)charnum[fgetc(fpwv)];

            if (ns == 0) {  // same as some previous group
                fscanf(fpwv, "%d\n", &kk);
                numsoln[d][k] = numsoln[d][kk];
                LUT[d][k] = LUT[d][kk];
            } else {
                fgetc(fpwv);  // '\n'
                numsoln[d][k] = ns;
                p = (struct csoln *)malloc(ns * sizeof(struct csoln));
                LUT[d][k] = p;
                for (i = 1; i <= ns; i++) {
                    linep = (unsigned char *)fgets((char *)line, 99, fpwv);
                    p->parent = charnum[*(linep++)];
                    j = 0;
                    while ((p->seg[j++] = charnum[*(linep++)]) != 0);
                    j = 10;
                    while ((p->seg[j--] = charnum[*(linep++)]) != 0);
#if FLUTEROUTING == 1
                    nn = 2 * d - 2;
                    ne = 2 * d - 3;
                    fread(line, 1, d - 2, fprt);
                    linep = line;
                    for (j = d; j < nn; j++) {
                        c = *(linep++);
                        if (c >= dsq) {
                            c -= dsq;
                            p->neighbor[divd[c]] = j;
                            ne--;
                        }
                        p->row[j - d] = divd[c];
                        p->col[j - d] = modd[c];
                        p->neighbor[j] = j;  // initialized
                    }
                    fread(line, 1, ne + 1, fprt);
                    linep = line;  // last char = \n
                    for (j = 0; j < ne; j++) {
                        c = *(linep++);
                        p->neighbor[div16[c]] = mod16[c];
                    }
#endif
                    p++;
                }
            }
        }
    }
}

Tree flute(int d, DTYPE x[], DTYPE y[], int acc) {
    unsigned allocateSize = MAXD;
    if (d > MAXD) {
        allocateSize = d + 1;
        //    printf("setting allocateSize = %d\n", allocateSize);
    }
    DTYPE *xs = (DTYPE *)malloc(sizeof(DTYPE) * allocateSize);
    DTYPE *ys = (DTYPE *)malloc(sizeof(DTYPE) * allocateSize);
    int *s = (int *)malloc(sizeof(int) * allocateSize);
    POINT *pt = (POINT *)malloc(sizeof(POINT) * allocateSize);
    POINTptr *ptp = (POINTptr *)malloc(sizeof(POINTptr) * allocateSize);

    POINT *tmpp;
    DTYPE minval;
    int i, j, minidx;
    Tree t;

    for (i = 0; i < d; i++) {
        pt[i].x = x[i];
        pt[i].y = y[i];
        ptp[i] = &pt[i];
    }

    // sort x
    for (i = 0; i < d - 1; i++) {
        minval = ptp[i]->x;
        minidx = i;
        for (j = i + 1; j < d; j++) {
            if (minval > ptp[j]->x ||
                (minval == ptp[j]->x &&
                 (ptp[minidx]->y > ptp[j]->y ||
                  (ptp[minidx]->y == ptp[j]->y && ptp[minidx] > ptp[j])))) {
                minval = ptp[j]->x;
                minidx = j;
            }
        }
        tmpp = ptp[i];
        ptp[i] = ptp[minidx];
        ptp[minidx] = tmpp;
    }

#if REMOVE_DUPLICATE_PIN == 1
    ptp[d] = &pt[d];
    ptp[d]->x = ptp[d]->y = -999999;
    j = 0;
    for (i = 0; i < d; i++) {
        for (k = i + 1; ptp[k]->x == ptp[i]->x; k++)
            if (ptp[k]->y == ptp[i]->y)  // pins k and i are the same
                break;
        if (ptp[k]->x != ptp[i]->x) ptp[j++] = ptp[i];
    }
    d = j;
#endif

    for (i = 0; i < d; i++) {
        xs[i] = ptp[i]->x;
        ptp[i]->o = i;
    }

    // sort y to find s[]
    for (i = 0; i < d - 1; i++) {
        minval = ptp[i]->y;
        minidx = i;
        for (j = i + 1; j < d; j++) {
            if (minval > ptp[j]->y ||
                (minval == ptp[j]->y &&
                 (ptp[minidx]->x > ptp[j]->x ||
                  (ptp[minidx]->x == ptp[j]->x && ptp[minidx] > ptp[j])))) {
                minval = ptp[j]->y;
                minidx = j;
            }
        }
        ys[i] = ptp[minidx]->y;
        s[i] = ptp[minidx]->o;
        ptp[minidx] = ptp[i];
    }
    ys[d - 1] = ptp[d - 1]->y;
    s[d - 1] = ptp[d - 1]->o;

    t = flutes(d, xs, ys, s, acc);

    free(xs);
    free(ys);
    free(s);
    free(pt);
    free(ptp);

    return t;
}

// xs[] and ys[] are coords in x and y in sorted order
// s[] is a list of nodes in increasing y direction
//   if nodes are indexed in the order of increasing x coord
//   i.e., s[i] = s_i in defined in paper
// The points are (xs[s[i]], ys[i]) for i=0..d-1
//             or (xs[i], ys[si[i]]) for i=0..d-1
// ZZ: RDP denotes Remove Duplicate Pin, simple, like std::unique
Tree flutes_RDP(int d, DTYPE xs[], DTYPE ys[], int s[], int acc) {
    int i, j, ss;

    for (i = 0; i < d - 1; i++) {
        if (xs[s[i]] == xs[s[i + 1]] && ys[i] == ys[i + 1]) {
            if (s[i] < s[i + 1])
                ss = s[i + 1];
            else {
                ss = s[i];
                s[i] = s[i + 1];
            }
            for (j = i + 2; j < d; j++) {
                ys[j - 1] = ys[j];
                s[j - 1] = s[j];
            }
            for (j = ss + 1; j < d; j++) xs[j - 1] = xs[j];
            for (j = 0; j <= d - 2; j++)
                if (s[j] > ss) s[j]--;
            i--;
            d--;
        }
    }
    return flutes_ALLD(d, xs, ys, s, acc);
}

// For low-degree, i.e., 2 <= d <= D
Tree flutes_LD(int d, DTYPE xs[], DTYPE ys[], int s[]) {
    int k, pi, i, j;
    struct csoln *rlist, *bestrlist;
    DTYPE dd[2 * D - 2];  // 0..D-2 for v, D-1..2*D-3 for h
    DTYPE minl, sum;
    DTYPE l[MPOWV + 1];
    int hflip;
    Tree t;

    t.deg = d;
    t.branch = (Branch *)malloc((2 * d - 2) * sizeof(Branch));
    if (d == 2) {
        // printf("s[0]=%d, s[1]=%d, xs[0,1]=[%u,%u], ys[0,1]=[%u,%u]\n",
        //        s[0], s[1], xs[0], xs[1], ys[0], ys[1]);
        minl = xs[1] - xs[0] + ys[1] - ys[0];
        t.branch[0].x = xs[s[0]];
        t.branch[0].y = ys[0];
        t.branch[0].n = 1;
        t.branch[1].x = xs[s[1]];
        t.branch[1].y = ys[1];
        t.branch[1].n = 1;
    } else if (d == 3) {
        minl = xs[2] - xs[0] + ys[2] - ys[0];
        t.branch[0].x = xs[s[0]];
        t.branch[0].y = ys[0];
        t.branch[0].n = 3;
        t.branch[1].x = xs[s[1]];
        t.branch[1].y = ys[1];
        t.branch[1].n = 3;
        t.branch[2].x = xs[s[2]];
        t.branch[2].y = ys[2];
        t.branch[2].n = 3;
        t.branch[3].x = xs[1];
        t.branch[3].y = ys[1];
        t.branch[3].n = 3;
    } else {
        k = 0;
        if (s[0] < s[2]) k++;
        if (s[1] < s[2]) k++;

        for (i = 3; i <= d - 1; i++) {  // p0=0 always, skip i=1 for symmetry
            pi = s[i];
            for (j = d - 1; j > i; j--)
                if (s[j] < s[i]) pi--;
            k = pi + (i + 1) * k;
        }

        if (k < numgrp[d]) {  // no horizontal flip
            hflip = 0;
            for (i = 1; i <= d - 3; i++) {
                dd[i] = ys[i + 1] - ys[i];
                dd[d - 1 + i] = xs[i + 1] - xs[i];
            }
        } else {
            hflip = 1;
            k = 2 * numgrp[d] - 1 - k;
            for (i = 1; i <= d - 3; i++) {
                dd[i] = ys[i + 1] - ys[i];
                dd[d - 1 + i] = xs[d - 1 - i] - xs[d - 2 - i];
            }
        }

        minl = l[0] = xs[d - 1] - xs[0] + ys[d - 1] - ys[0];
        rlist = LUT[d][k];
        for (i = 0; rlist->seg[i] > 0; i++) minl += dd[rlist->seg[i]];
        bestrlist = rlist;
        l[1] = minl;
        j = 2;
        while (j <= numsoln[d][k]) {
            rlist++;
            sum = l[rlist->parent];
            for (i = 0; rlist->seg[i] > 0; i++) sum += dd[rlist->seg[i]];
            for (i = 10; rlist->seg[i] > 0; i--) sum -= dd[rlist->seg[i]];
            if (sum < minl) {
                minl = sum;
                bestrlist = rlist;
            }
            l[j++] = sum;
        }

        t.branch[0].x = xs[s[0]];
        t.branch[0].y = ys[0];
        t.branch[1].x = xs[s[1]];
        t.branch[1].y = ys[1];
        for (i = 2; i < d - 2; i++) {
            t.branch[i].x = xs[s[i]];
            t.branch[i].y = ys[i];
            t.branch[i].n = bestrlist->neighbor[i];
        }
        t.branch[d - 2].x = xs[s[d - 2]];
        t.branch[d - 2].y = ys[d - 2];
        t.branch[d - 1].x = xs[s[d - 1]];
        t.branch[d - 1].y = ys[d - 1];
        if (hflip) {
            if (s[1] < s[0]) {
                t.branch[0].n = bestrlist->neighbor[1];
                t.branch[1].n = bestrlist->neighbor[0];
            } else {
                t.branch[0].n = bestrlist->neighbor[0];
                t.branch[1].n = bestrlist->neighbor[1];
            }
            if (s[d - 1] < s[d - 2]) {
                t.branch[d - 2].n = bestrlist->neighbor[d - 1];
                t.branch[d - 1].n = bestrlist->neighbor[d - 2];
            } else {
                t.branch[d - 2].n = bestrlist->neighbor[d - 2];
                t.branch[d - 1].n = bestrlist->neighbor[d - 1];
            }
            for (i = d; i < 2 * d - 2; i++) {
                t.branch[i].x = xs[d - 1 - bestrlist->col[i - d]];
                t.branch[i].y = ys[bestrlist->row[i - d]];
                t.branch[i].n = bestrlist->neighbor[i];
            }
        } else {  // !hflip
            if (s[0] < s[1]) {
                t.branch[0].n = bestrlist->neighbor[1];
                t.branch[1].n = bestrlist->neighbor[0];
            } else {
                t.branch[0].n = bestrlist->neighbor[0];
                t.branch[1].n = bestrlist->neighbor[1];
            }
            if (s[d - 2] < s[d - 1]) {
                t.branch[d - 2].n = bestrlist->neighbor[d - 1];
                t.branch[d - 1].n = bestrlist->neighbor[d - 2];
            } else {
                t.branch[d - 2].n = bestrlist->neighbor[d - 2];
                t.branch[d - 1].n = bestrlist->neighbor[d - 1];
            }
            for (i = d; i < 2 * d - 2; i++) {
                t.branch[i].x = xs[bestrlist->col[i - d]];
                t.branch[i].y = ys[bestrlist->row[i - d]];
                t.branch[i].n = bestrlist->neighbor[i];
            }
        }
    }
    t.length = minl;

    return t;
}

// For medium-degree, i.e., D+1 <= d <= D2
Tree flutes_MD(int d, DTYPE xs[], DTYPE ys[], int s[], int acc) {
    unsigned allocateSize = MAXD;
    if (d > MAXD) allocateSize = d + 1;
    DTYPE *x1 = (DTYPE *)malloc(sizeof(DTYPE) * allocateSize);
    DTYPE *x2 = (DTYPE *)malloc(sizeof(DTYPE) * allocateSize);
    DTYPE *y1 = (DTYPE *)malloc(sizeof(DTYPE) * allocateSize);
    DTYPE *y2 = (DTYPE *)malloc(sizeof(DTYPE) * allocateSize);
    int *si = (int *)malloc(sizeof(int) * allocateSize);
    int *s1 = (int *)malloc(sizeof(int) * allocateSize);
    int *s2 = (int *)malloc(sizeof(int) * allocateSize);
    float *score = (float *)malloc(sizeof(float) * 2 * allocateSize);
    float *penalty = (float *)malloc(sizeof(float) * allocateSize);
    DTYPE *distx = (DTYPE *)malloc(sizeof(DTYPE) * allocateSize);
    DTYPE *disty = (DTYPE *)malloc(sizeof(DTYPE) * allocateSize);

    //  DTYPE x1[MAXD], x2[MAXD], y1[MAXD], y2[MAXD];
    //  int si[MAXD], s1[MAXD], s2[MAXD];
    //  float score[2*MAXD], penalty[MAXD];
    //  DTYPE distx[MAXD], disty[MAXD];
    float pnlty, dx, dy;
    DTYPE ll, minl, coord1, coord2;
    int i, r, p, maxbp, bestbp, bp, nbp, ub, lb, n1, n2, nn1, nn2, ms, newacc;
    Tree t, t1, t2, bestt1, bestt2;
    int mins, maxs, minsi, maxsi;
    DTYPE xydiff;

    for (i = 0; i < (int)allocateSize; ++i) {
        distx[i] = disty[i] = 0;
    }

    if (s[0] < s[d - 1]) {
        ms = max(s[0], s[1]);
        for (i = 2; i <= ms; i++) ms = max(ms, s[i]);
        if (ms <= d - 3) {
            for (i = 0; i <= ms; i++) {
                x1[i] = xs[i];
                y1[i] = ys[i];
                s1[i] = s[i];
            }
            x1[ms + 1] = xs[ms];
            y1[ms + 1] = ys[ms];
            s1[ms + 1] = ms + 1;

            s2[0] = 0;
            for (i = 1; i <= d - 1 - ms; i++) s2[i] = s[i + ms] - ms;

            t1 = flutes_LMD(ms + 2, x1, y1, s1, acc);
            t2 = flutes_LMD(d - ms, xs + ms, ys + ms, s2, acc);
            t = dmergetree(t1, t2);
            free(t1.branch);
            free(t2.branch);

            free(x1);
            free(x2);
            free(y1);
            free(y2);
            free(si);
            free(s1);
            free(s2);
            free(score);
            free(penalty);
            free(distx);
            free(disty);
            return t;
        }
    } else {  // (s[0] > s[d-1])
        ms = min(s[0], s[1]);
        for (i = 2; i <= d - 1 - ms; i++) ms = min(ms, s[i]);
        if (ms >= 2) {
            x1[0] = xs[ms];
            y1[0] = ys[0];
            s1[0] = s[0] - ms + 1;
            for (i = 1; i <= d - 1 - ms; i++) {
                x1[i] = xs[i + ms - 1];
                y1[i] = ys[i];
                s1[i] = s[i] - ms + 1;
            }
            x1[d - ms] = xs[d - 1];
            y1[d - ms] = ys[d - 1 - ms];
            s1[d - ms] = 0;

            s2[0] = ms;
            for (i = 1; i <= ms; i++) s2[i] = s[i + d - 1 - ms];

            t1 = flutes_LMD(d + 1 - ms, x1, y1, s1, acc);
            t2 = flutes_LMD(ms + 1, xs, ys + d - 1 - ms, s2, acc);
            t = dmergetree(t1, t2);
            free(t1.branch);
            free(t2.branch);

            free(x1);
            free(x2);
            free(y1);
            free(y2);
            free(si);
            free(s1);
            free(s2);
            free(score);
            free(penalty);
            free(distx);
            free(disty);
            return t;
        }
    }

    // Find inverse si[] of s[]
    for (r = 0; r < d; r++) si[s[r]] = r;

    // Determine breaking directions and positions dp[]
    lb = max((d - acc) / 5, 2);
    ub = d - 1 - lb;

    // Compute scores
#define AA 0.6  // 2.0*BB
#define BB 0.3
    // #define CCC max(0.425-0.005*d-0.015*acc, 0.1)
    // #define CCC max(0.43-0.005*d-0.01*acc, 0.1)
#define CCC max(0.41 - 0.005 * d, 0.1)
#define DD 4.8
    float DDD = DD / (d - 1);

    // Compute penalty[]
    dx = CCC * (xs[d - 2] - xs[1]) / (d - 3);
    dy = CCC * (ys[d - 2] - ys[1]) / (d - 3);
    for (r = d / 2, pnlty = 0; r >= 2; r--, pnlty += dx)
        penalty[r] = pnlty, penalty[d - 1 - r] = pnlty;
    penalty[1] = pnlty, penalty[d - 2] = pnlty;
    penalty[0] = pnlty, penalty[d - 1] = pnlty;
    for (r = d / 2 - 1, pnlty = dy; r >= 2; r--, pnlty += dy)
        penalty[s[r]] += pnlty, penalty[s[d - 1 - r]] += pnlty;
    penalty[s[1]] += pnlty, penalty[s[d - 2]] += pnlty;
    penalty[s[0]] += pnlty, penalty[s[d - 1]] += pnlty;
    // #define CC 0.16
    // #define v(r) ((r==0||r==1||r==d-2||r==d-1) ? d-3 : abs(d-1-r-r))
    //     for (r=0; r<d; r++)
    //         penalty[r] = v(r)*dx + v(si[r])*dy;

    // Compute distx[], disty[]
    xydiff = (xs[d - 1] - xs[0]) - (ys[d - 1] - ys[0]);
    if (s[0] < s[1])
        mins = s[0], maxs = s[1];
    else
        mins = s[1], maxs = s[0];
    if (si[0] < si[1])
        minsi = si[0], maxsi = si[1];
    else
        minsi = si[1], maxsi = si[0];
    for (r = 2; r <= ub; r++) {
        if (s[r] < mins)
            mins = s[r];
        else if (s[r] > maxs)
            maxs = s[r];
        distx[r] = xs[maxs] - xs[mins];
        if (si[r] < minsi)
            minsi = si[r];
        else if (si[r] > maxsi)
            maxsi = si[r];
        disty[r] = ys[maxsi] - ys[minsi] + xydiff;
    }

    if (s[d - 2] < s[d - 1])
        mins = s[d - 2], maxs = s[d - 1];
    else
        mins = s[d - 1], maxs = s[d - 2];
    if (si[d - 2] < si[d - 1])
        minsi = si[d - 2], maxsi = si[d - 1];
    else
        minsi = si[d - 1], maxsi = si[d - 2];
    for (r = d - 3; r >= lb; r--) {
        if (s[r] < mins)
            mins = s[r];
        else if (s[r] > maxs)
            maxs = s[r];
        distx[r] += xs[maxs] - xs[mins];
        if (si[r] < minsi)
            minsi = si[r];
        else if (si[r] > maxsi)
            maxsi = si[r];
        disty[r] += ys[maxsi] - ys[minsi];
    }

    nbp = 0;
    for (r = lb; r <= ub; r++) {
        if (si[r] <= 1)
            score[nbp] = (xs[r + 1] - xs[r - 1]) - penalty[r] -
                         AA * (ys[2] - ys[1]) - DDD * disty[r];
        else if (si[r] >= d - 2)
            score[nbp] = (xs[r + 1] - xs[r - 1]) - penalty[r] -
                         AA * (ys[d - 2] - ys[d - 3]) - DDD * disty[r];
        else
            score[nbp] = (xs[r + 1] - xs[r - 1]) - penalty[r] -
                         BB * (ys[si[r] + 1] - ys[si[r] - 1]) - DDD * disty[r];
        nbp++;

        if (s[r] <= 1)
            score[nbp] = (ys[r + 1] - ys[r - 1]) - penalty[s[r]] -
                         AA * (xs[2] - xs[1]) - DDD * distx[r];
        else if (s[r] >= d - 2)
            score[nbp] = (ys[r + 1] - ys[r - 1]) - penalty[s[r]] -
                         AA * (xs[d - 2] - xs[d - 3]) - DDD * distx[r];
        else
            score[nbp] = (ys[r + 1] - ys[r - 1]) - penalty[s[r]] -
                         BB * (xs[s[r] + 1] - xs[s[r] - 1]) - DDD * distx[r];
        nbp++;
    }

    if (acc <= 3)
        newacc = 1;
    else {
        newacc = acc / 2;
        if (acc >= nbp) acc = nbp - 1;
    }

    minl = (DTYPE)INT_MAX;
    bestt1.branch = bestt2.branch = NULL;
    for (i = 0; i < acc; i++) {
        maxbp = 0;
        for (bp = 1; bp < nbp; bp++)
            if (score[maxbp] < score[bp]) maxbp = bp;
        score[maxbp] = -9e9f;

#define BreakPt(bp) ((bp) / 2 + lb)
#define BreakInX(bp) ((bp) % 2 == 0)
        p = BreakPt(maxbp);
        // Breaking in p
        if (BreakInX(maxbp)) {  // break in x
            n1 = n2 = 0;
            for (r = 0; r < d; r++) {
                if (s[r] < p) {
                    s1[n1] = s[r];
                    y1[n1] = ys[r];
                    n1++;
                } else if (s[r] > p) {
                    s2[n2] = s[r] - p;
                    y2[n2] = ys[r];
                    n2++;
                } else {  // if (s[r] == p)  i.e.,  r = si[p]
                    s1[n1] = p;
                    s2[n2] = 0;
                    y1[n1] = y2[n2] = ys[r];
                    nn1 = n1;
                    nn2 = n2;
                    n1++;
                    n2++;
                }
            }

            t1 = flutes_LMD(p + 1, xs, y1, s1, newacc);
            t2 = flutes_LMD(d - p, xs + p, y2, s2, newacc);
            ll = t1.length + t2.length;
            coord1 = t1.branch[t1.branch[nn1].n].y;
            coord2 = t2.branch[t2.branch[nn2].n].y;
            if (t2.branch[nn2].y > max(coord1, coord2))
                ll -= t2.branch[nn2].y - max(coord1, coord2);
            else if (t2.branch[nn2].y < min(coord1, coord2))
                ll -= min(coord1, coord2) - t2.branch[nn2].y;
        } else {  // if (!BreakInX(maxbp))
            n1 = n2 = 0;
            for (r = 0; r < d; r++) {
                if (si[r] < p) {
                    s1[si[r]] = n1;
                    x1[n1] = xs[r];
                    n1++;
                } else if (si[r] > p) {
                    s2[si[r] - p] = n2;
                    x2[n2] = xs[r];
                    n2++;
                } else {  // if (si[r] == p)  i.e.,  r = s[p]
                    s1[p] = n1;
                    s2[0] = n2;
                    x1[n1] = x2[n2] = xs[r];
                    n1++;
                    n2++;
                }
            }

            t1 = flutes_LMD(p + 1, x1, ys, s1, newacc);
            t2 = flutes_LMD(d - p, x2, ys + p, s2, newacc);
            ll = t1.length + t2.length;
            coord1 = t1.branch[t1.branch[p].n].x;
            coord2 = t2.branch[t2.branch[0].n].x;
            if (t2.branch[0].x > max(coord1, coord2))
                ll -= t2.branch[0].x - max(coord1, coord2);
            else if (t2.branch[0].x < min(coord1, coord2))
                ll -= min(coord1, coord2) - t2.branch[0].x;
        }
        if (minl > ll) {
            minl = ll;
            free(bestt1.branch);
            free(bestt2.branch);
            bestt1 = t1;
            bestt2 = t2;
            bestbp = maxbp;
        } else {
            free(t1.branch);
            free(t2.branch);
        }
    }

    if (BreakInX(bestbp))
        t = hmergetree(bestt1, bestt2, s);
    else
        t = vmergetree(bestt1, bestt2);
    free(bestt1.branch);
    free(bestt2.branch);

    free(x1);
    free(x2);
    free(y1);
    free(y2);
    free(si);
    free(s1);
    free(s2);
    free(score);
    free(penalty);
    free(distx);
    free(disty);
    return t;
}

Tree dmergetree(Tree t1, Tree t2) {
    int i, d, prev, curr, next, offset1, offset2;
    Tree t;

    t.deg = d = t1.deg + t2.deg - 2;
    t.length = t1.length + t2.length;
    t.branch = (Branch *)malloc((2 * d - 2) * sizeof(Branch));
    offset1 = t2.deg - 2;
    offset2 = 2 * t1.deg - 4;

    for (i = 0; i <= t1.deg - 2; i++) {
        t.branch[i].x = t1.branch[i].x;
        t.branch[i].y = t1.branch[i].y;
        t.branch[i].n = t1.branch[i].n + offset1;
    }
    for (i = t1.deg - 1; i <= d - 1; i++) {
        t.branch[i].x = t2.branch[i - t1.deg + 2].x;
        t.branch[i].y = t2.branch[i - t1.deg + 2].y;
        t.branch[i].n = t2.branch[i - t1.deg + 2].n + offset2;
    }
    for (i = d; i <= d + t1.deg - 3; i++) {
        t.branch[i].x = t1.branch[i - offset1].x;
        t.branch[i].y = t1.branch[i - offset1].y;
        t.branch[i].n = t1.branch[i - offset1].n + offset1;
    }
    for (i = d + t1.deg - 2; i <= 2 * d - 3; i++) {
        t.branch[i].x = t2.branch[i - offset2].x;
        t.branch[i].y = t2.branch[i - offset2].y;
        t.branch[i].n = t2.branch[i - offset2].n + offset2;
    }

    prev = t2.branch[0].n + offset2;
    curr = t1.branch[t1.deg - 1].n + offset1;
    next = t.branch[curr].n;
    while (curr != next) {
        t.branch[curr].n = prev;
        prev = curr;
        curr = next;
        next = t.branch[curr].n;
    }
    t.branch[curr].n = prev;

    return t;
}

Tree hmergetree(Tree t1, Tree t2, int s[]) {
    int i, prev, curr, next, extra, offset1, offset2;
    int p, ii, n1, n2, nn1, nn2;
    DTYPE coord1, coord2;
    Tree t;

    t.deg = t1.deg + t2.deg - 1;
    t.length = t1.length + t2.length;
    t.branch = (Branch *)malloc((2 * t.deg - 2) * sizeof(Branch));
    offset1 = t2.deg - 1;
    offset2 = 2 * t1.deg - 3;

    p = t1.deg - 1;
    n1 = n2 = 0;
    for (i = 0; i < t.deg; i++) {
        if (s[i] < p) {
            t.branch[i].x = t1.branch[n1].x;
            t.branch[i].y = t1.branch[n1].y;
            t.branch[i].n = t1.branch[n1].n + offset1;
            n1++;
        } else if (s[i] > p) {
            t.branch[i].x = t2.branch[n2].x;
            t.branch[i].y = t2.branch[n2].y;
            t.branch[i].n = t2.branch[n2].n + offset2;
            n2++;
        } else {
            t.branch[i].x = t2.branch[n2].x;
            t.branch[i].y = t2.branch[n2].y;
            t.branch[i].n = t2.branch[n2].n + offset2;
            nn1 = n1;
            nn2 = n2;
            ii = i;
            n1++;
            n2++;
        }
    }
    for (i = t.deg; i <= t.deg + t1.deg - 3; i++) {
        t.branch[i].x = t1.branch[i - offset1].x;
        t.branch[i].y = t1.branch[i - offset1].y;
        t.branch[i].n = t1.branch[i - offset1].n + offset1;
    }
    for (i = t.deg + t1.deg - 2; i <= 2 * t.deg - 4; i++) {
        t.branch[i].x = t2.branch[i - offset2].x;
        t.branch[i].y = t2.branch[i - offset2].y;
        t.branch[i].n = t2.branch[i - offset2].n + offset2;
    }
    extra = 2 * t.deg - 3;
    coord1 = t1.branch[t1.branch[nn1].n].y;
    coord2 = t2.branch[t2.branch[nn2].n].y;
    if (t2.branch[nn2].y > max(coord1, coord2)) {
        t.branch[extra].y = max(coord1, coord2);
        t.length -= t2.branch[nn2].y - t.branch[extra].y;
    } else if (t2.branch[nn2].y < min(coord1, coord2)) {
        t.branch[extra].y = min(coord1, coord2);
        t.length -= t.branch[extra].y - t2.branch[nn2].y;
    } else
        t.branch[extra].y = t2.branch[nn2].y;
    t.branch[extra].x = t2.branch[nn2].x;
    t.branch[extra].n = t.branch[ii].n;
    t.branch[ii].n = extra;

    prev = extra;
    curr = t1.branch[nn1].n + offset1;
    next = t.branch[curr].n;
    while (curr != next) {
        t.branch[curr].n = prev;
        prev = curr;
        curr = next;
        next = t.branch[curr].n;
    }
    t.branch[curr].n = prev;

    return t;
}

Tree vmergetree(Tree t1, Tree t2) {
    int i, prev, curr, next, extra, offset1, offset2;
    DTYPE coord1, coord2;
    Tree t;

    t.deg = t1.deg + t2.deg - 1;
    t.length = t1.length + t2.length;
    t.branch = (Branch *)malloc((2 * t.deg - 2) * sizeof(Branch));
    offset1 = t2.deg - 1;
    offset2 = 2 * t1.deg - 3;

    for (i = 0; i <= t1.deg - 2; i++) {
        t.branch[i].x = t1.branch[i].x;
        t.branch[i].y = t1.branch[i].y;
        t.branch[i].n = t1.branch[i].n + offset1;
    }
    for (i = t1.deg - 1; i <= t.deg - 1; i++) {
        t.branch[i].x = t2.branch[i - t1.deg + 1].x;
        t.branch[i].y = t2.branch[i - t1.deg + 1].y;
        t.branch[i].n = t2.branch[i - t1.deg + 1].n + offset2;
    }
    for (i = t.deg; i <= t.deg + t1.deg - 3; i++) {
        t.branch[i].x = t1.branch[i - offset1].x;
        t.branch[i].y = t1.branch[i - offset1].y;
        t.branch[i].n = t1.branch[i - offset1].n + offset1;
    }
    for (i = t.deg + t1.deg - 2; i <= 2 * t.deg - 4; i++) {
        t.branch[i].x = t2.branch[i - offset2].x;
        t.branch[i].y = t2.branch[i - offset2].y;
        t.branch[i].n = t2.branch[i - offset2].n + offset2;
    }
    extra = 2 * t.deg - 3;
    coord1 = t1.branch[t1.branch[t1.deg - 1].n].x;
    coord2 = t2.branch[t2.branch[0].n].x;
    if (t2.branch[0].x > max(coord1, coord2)) {
        t.branch[extra].x = max(coord1, coord2);
        t.length -= t2.branch[0].x - t.branch[extra].x;
    } else if (t2.branch[0].x < min(coord1, coord2)) {
        t.branch[extra].x = min(coord1, coord2);
        t.length -= t.branch[extra].x - t2.branch[0].x;
    } else
        t.branch[extra].x = t2.branch[0].x;
    t.branch[extra].y = t2.branch[0].y;
    t.branch[extra].n = t.branch[t1.deg - 1].n;
    t.branch[t1.deg - 1].n = extra;

    prev = extra;
    curr = t1.branch[t1.deg - 1].n + offset1;
    next = t.branch[curr].n;
    while (curr != next) {
        t.branch[curr].n = prev;
        prev = curr;
        curr = next;
        next = t.branch[curr].n;
    }
    t.branch[curr].n = prev;

    return t;
}

int main(int argc, const char **argv) {
    if (argc != 3) {
        printf("usage: %s <input.bin> <output.bin>\n", argv[0]);
        return 255;
    }
    readLUT();

    FILE *input_fp = fopen(argv[1], "rb");
    assert(input_fp);
    fseek(input_fp, 0, SEEK_END);
    unsigned long input_bin_size = ftell(input_fp);
    fseek(input_fp, 0, SEEK_SET);
    int *buf_input = (int *)malloc(input_bin_size);
    assert(fread(buf_input, 1, input_bin_size, input_fp) == input_bin_size);
    fclose(input_fp);

    int num_nets = buf_input[0];
    int *pin_st = buf_input + 1;
    int tot_num_pins = pin_st[num_nets];
    DTYPE *data_x = (DTYPE *)(pin_st + num_nets + 1);
    DTYPE *data_y = (DTYPE *)(data_x + tot_num_pins);

    DTYPE *result_x = (DTYPE *)calloc(tot_num_pins * 2, sizeof(DTYPE));
    DTYPE *result_y = (DTYPE *)calloc(tot_num_pins * 2, sizeof(DTYPE));
    int *result_n = (int *)calloc(tot_num_pins * 2, sizeof(int));

    for (int net_i = 0; net_i < num_nets; ++net_i) {
        Tree t =
            flute(pin_st[net_i + 1] - pin_st[net_i], data_x + pin_st[net_i],
                  data_y + pin_st[net_i], ACCURACY);
        // printf("%d %d\n", t.deg, t.length);
        // for(int i = 0; i < 2 * t.deg - 2; ++i) {
        //   printf("%d %d %d\n", t.branch[i].x, t.branch[i].y, t.branch[i].n);
        // }
        int offset = pin_st[net_i] * 2;
        for (int i = 0; i < 2 * t.deg - 2; ++i) {
            result_x[offset + i] = t.branch[i].x;
            result_y[offset + i] = t.branch[i].y;
            result_n[offset + i] = t.branch[i].n;
        }
        free(t.branch);
    }

    FILE *output_fp = fopen(argv[2], "wb");
    assert(output_fp);
    fwrite(result_x, sizeof(DTYPE), tot_num_pins, output_fp);
    fwrite(result_y, sizeof(DTYPE), tot_num_pins, output_fp);
    fwrite(result_n, sizeof(int), tot_num_pins, output_fp);
    fclose(output_fp);

    free(result_x);
    free(result_y);
    free(result_n);
    free(buf_input);
    return 0;
}