// start of spasm-master/src/spasm.h
#ifndef _SPASM_H
#define _SPASM_H

#include <stddef.h>           // size_t
#include <inttypes.h>         // int64_t
#include <stdio.h>            // FILE
#include <stdbool.h>

typedef uint8_t u8;
typedef int64_t i64;
typedef uint64_t u64;
typedef uint32_t u32;
typedef int32_t i32;


#ifdef _OPENMP
#include <omp.h>
#endif

#define SPASM_VERSION "1.3"
#define SPASM_BUG_ADDRESS "<charles.bouillaguet@lip6.fr>"


/* --- primary struct spasm_csr routines and data structures --- */

// unfortunately we use "n" for #rows and "m" for #columns whereas the rest of the world (BLAS...)
// does the opposite... 

typedef i32 spasm_ZZp;

struct spasm_field_struct {
	i64 p;
    i64 halfp;
    i64 mhalfp;
    double dinvp;
};
typedef struct spasm_field_struct spasm_field[1];

struct spasm_csr {                /* matrix in compressed-sparse row format */
	i64 nzmax;                    /* maximum number of entries */
	int n;                        /* number of rows */
	int m;                        /* number of columns */
	i64 *p;                       /* row pointers (size n+1) */
	int *j;                       /* column indices, size nzmax */
	spasm_ZZp *x;                 /* numerical values, size nzmax (optional) */
	spasm_field field;
	/*
	 * The actual number of entries is p[n]. 
	 * Coefficients of a row need not be sorted by column index.
	 * The numerical values are optional (useful for storing a sparse graph, or the pattern of a matrix).
	 */
};

struct spasm_triplet {             /* matrix in triplet form */
	i64 nzmax;                     /* maximum number of entries */
	i64 nz;                        /* # entries */
	int n;                         /* number of rows */
	int m;                         /* number of columns */
	int *i;                        /* row indices, size nzmax */
	int *j;                        /* column indices (size nzmax) */
	spasm_ZZp *x;                  /* numerical values, size nzmax (optional) */
	spasm_field field;
};

struct spasm_lu {                  /* a PLUQ factorisation */
	int r;                         /* rank of the input matrix */
	bool complete;                 /* if L != NULL, indicates whether A == L*U */
	struct spasm_csr *L;
	struct spasm_csr *U;
	int *qinv;                     /* locate pivots in U (on column j, row qinv[j]) */
	int *p;                        /* locate pivots in L (on column j, row p[j]) */
	struct spasm_triplet *Ltmp;           /* for internal use during the factorization */
};

struct spasm_dm {      /**** a Dulmage-Mendelson decomposition */
				int *p;       /* size n, row permutation */
				int *q;       /* size m, column permutation */
				int *r;       /* size nb+1, block k is rows r[k] to r[k+1]-1 in A(p,q) */
				int *c;       /* size nb+1, block k is cols s[k] to s[k+1]-1 in A(p,q) */
				int nb;       /* # of blocks in fine decomposition */
				int rr[5];    /* coarse row decomposition */
				int cc[5];    /* coarse column decomposition */
};

struct echelonize_opts {
	/* pivot search sub-algorithms */
	bool enable_greedy_pivot_search;

	/* echelonization sub-algorithms */
	bool enable_tall_and_skinny;
	bool enable_dense;
	bool enable_GPLU;

	/* Parameters of the "root" echelonization procedure itself */
	bool L;                         /* should we compute L / Lp in addition to U / Uqinv ? */
	bool complete;                  /* A == LU / otherwise L is just OK for the pivotal rows */
	double min_pivot_proportion;    /* minimum number of pivots found to keep going; < 0 = keep going */
	int max_round;                  /* maximum number of rounds; < 0 = keep going */
 
 	/* Parameters that determine the choice of a finalization strategy */
 	double sparsity_threshold;      /* denser than this --> dense method; < 0 = keep going */

	/* options of dense methods */
	int dense_block_size;           /* #rows processed in each batch; determine memory consumption */
	double low_rank_ratio;          /* if k rows have rank less than k * low_rank_ratio --> "tall-and-skinny"; <0 = don't */
	double tall_and_skinny_ratio;   /* aspect ratio (#rows / #cols) higher than this --> "tall-and-skinny"; <0 = don't */
	double low_rank_start_weight;   /* compute random linear combinations of this many rows; -1 = auto-select */

};

struct spasm_rank_certificate {
	int r;
	i64 prime;
	u8 hash[32];
	int *i;           /* size r */
	int *j;           /* size r */
	spasm_ZZp *x;     /* size r */
	spasm_ZZp *y;     /* size r */
};

typedef struct {
    u32 h[8];
    u32 Nl, Nh;
    u32 data[16];
    u32 num, md_len;
} spasm_sha256_ctx;

typedef struct {
        u32 block[11];   /* block[0:8] == H(matrix); block[8] = prime; block[9] = ctx, block[10] = seq */
        u32 hash[8];
        u32 prime;
        u32 mask;        /* 2^i - 1 where i is the smallest s.t. 2^i > prime */
        int counter;
        int i;
        spasm_field field;
} spasm_prng_ctx;

typedef enum {SPASM_DOUBLE, SPASM_FLOAT, SPASM_I64} spasm_datatype;

#define SPASM_IDENTITY_PERMUTATION NULL
#define SPASM_IGNORE NULL
#define SPASM_IGNORE_VALUES 0

/* spasm_ZZp.c */
void spasm_field_init(i64 p, spasm_field F);
spasm_ZZp spasm_ZZp_init(const spasm_field F, i64 x);
spasm_ZZp spasm_ZZp_add(const spasm_field F, spasm_ZZp a, spasm_ZZp b);
spasm_ZZp spasm_ZZp_sub(const spasm_field F, spasm_ZZp a, spasm_ZZp b);
spasm_ZZp spasm_ZZp_mul(const spasm_field F, spasm_ZZp a, spasm_ZZp b);
spasm_ZZp spasm_ZZp_inverse(const spasm_field F, spasm_ZZp a);
spasm_ZZp spasm_ZZp_axpy(const spasm_field F, spasm_ZZp a, spasm_ZZp x, spasm_ZZp y);

/* sha256.c */
void spasm_SHA256_init(spasm_sha256_ctx *c);
void spasm_SHA256_update(spasm_sha256_ctx *c, const void *data, size_t len);
void spasm_SHA256_final(u8 *md, spasm_sha256_ctx *c);

/* spasm_prng.c */
void spasm_prng_seed(const u8 *seed, i64 prime, u32 seq, spasm_prng_ctx *ctx);
void spasm_prng_seed_simple(i64 prime, u64 seed, u32 seq, spasm_prng_ctx *ctx);
u32 spasm_prng_u32(spasm_prng_ctx *ctx);
spasm_ZZp spasm_prng_ZZp(spasm_prng_ctx *ctx);

/* spasm_util.c */
double spasm_wtime();
i64 spasm_nnz(const struct spasm_csr * A);
void *spasm_malloc(i64 size);
void *spasm_calloc(i64 count, i64 size);
void *spasm_realloc(void *ptr, i64 size);
struct spasm_csr *spasm_csr_alloc(int n, int m, i64 nzmax, i64 prime, bool with_values);
void spasm_csr_realloc(struct spasm_csr * A, i64 nzmax);
void spasm_csr_resize(struct spasm_csr * A, int n, int m);
void spasm_csr_free(struct spasm_csr * A);
struct spasm_triplet *spasm_triplet_alloc(int m, int n, i64 nzmax, i64 prime, bool with_values);
void spasm_triplet_realloc(struct spasm_triplet * A, i64 nzmax);
void spasm_triplet_free(struct spasm_triplet * A);
struct spasm_dm *spasm_dm_alloc(int n, int m);
void spasm_dm_free(struct spasm_dm * P);
void spasm_lu_free(struct spasm_lu *N);
void spasm_human_format(int64_t n, char *target);
int spasm_get_num_threads();
int spasm_get_thread_num();
static inline i64 spasm_get_prime(const struct spasm_csr *A) { return A->field->p; }

/* spasm_triplet.c */
void spasm_add_entry(struct spasm_triplet *T, int i, int j, i64 x);
void spasm_triplet_transpose(struct spasm_triplet * T);
struct spasm_csr *spasm_compress(const struct spasm_triplet * T);

/* spasm_io.c */
struct spasm_triplet *spasm_triplet_load(FILE * f, i64 prime, u8 *hash);
void spasm_triplet_save(const struct spasm_triplet * A, FILE * f);
void spasm_csr_save(const struct spasm_csr * A, FILE * f);
void spasm_save_pnm(const struct spasm_csr * A, FILE * f, int x, int y, int mode, struct spasm_dm *DM);

/* spasm_transpose.c */
struct spasm_csr *spasm_transpose(const struct spasm_csr * C, int keep_values);

/* spasm_submatrix.c */
struct spasm_csr *spasm_submatrix(const struct spasm_csr * A, int r_0, int r_1, int c_0, int c_1, int with_values);

/* spasm_permutation.c */
void spasm_pvec(const int *p, const spasm_ZZp * b, spasm_ZZp * x, int n);
void spasm_ipvec(const int *p, const spasm_ZZp * b, spasm_ZZp * x, int n);
int *spasm_pinv(int const *p, int n);
struct spasm_csr *spasm_permute(const struct spasm_csr * A, const int *p, const int *qinv, int with_values);
int *spasm_random_permutation(int n);
void spasm_range_pvec(int *x, int a, int b, int *p);

/* spasm_scatter.c */
void spasm_scatter(const struct spasm_csr *A, int i, spasm_ZZp beta, spasm_ZZp * x)
{
	const i64 *Ap = A->p;
	const int *Aj = A->j;
	const spasm_ZZp *Ax = A->x;
	for (i64 px = Ap[i]; px < Ap[i + 1]; px++) {
		int j = Aj[px];
		x[j] = spasm_ZZp_axpy(A->field, beta, Ax[px], x[j]);
	}
}


/* spasm_reach.c */
int spasm_dfs(int i, const struct spasm_csr * G, int top, int *xi, int *pstack, int *marks, const int *pinv);
int spasm_reach(const struct spasm_csr * A, const struct spasm_csr * B, int k, int l, int *xj, const int *qinv);

/* spasm_spmv.c */
void spasm_xApy(const spasm_ZZp *x, const struct spasm_csr *A, spasm_ZZp *y);
void spasm_Axpy(const struct spasm_csr *A, const spasm_ZZp *x, spasm_ZZp *y);

/* spasm_triangular.c */
void spasm_dense_back_solve(const struct spasm_csr *L, spasm_ZZp *b, spasm_ZZp *x, const int *p);
bool spasm_dense_forward_solve(const struct spasm_csr * U, spasm_ZZp * b, spasm_ZZp * x, const int *q);
int spasm_sparse_triangular_solve(const struct spasm_csr *U, const struct spasm_csr *B, int k, int *xj, spasm_ZZp * x, const int *qinv);

/* spasm_schur.c */
struct spasm_csr *spasm_schur(const struct spasm_csr *A, const int *p, int n, const struct spasm_lu *fact, 
                   double est_density, struct spasm_triplet *L, const int *p_in, int *p_out);
double spasm_schur_estimate_density(const struct spasm_csr * A, const int *p, int n, const struct spasm_csr *U, const int *qinv, int R);
void spasm_schur_dense(const struct spasm_csr *A, const int *p, int n, const int *p_in, 
	struct spasm_lu *fact, void *S, spasm_datatype datatype,int *q, int *p_out);
void spasm_schur_dense_randomized(const struct spasm_csr *A, const int *p, int n, const struct spasm_csr *U, const int *qinv, 
	void *S, spasm_datatype datatype, int *q, int N, int w);

/* spasm_pivots.c */
int spasm_pivots_extract_structural(const struct spasm_csr *A, const int *p_in, struct spasm_lu *fact, int *p, struct echelonize_opts *opts);

/* spasm_matching.c */
int spasm_maximum_matching(const struct spasm_csr *A, int *jmatch, int *imatch);
int *spasm_permute_row_matching(int n, const int *jmatch, const int *p, const int *qinv);
int *spasm_permute_column_matching(int m, const int *imatch, const int *pinv, const int *q);
int *spasm_submatching(const int *match, int a, int b, int c, int d);
int spasm_structural_rank(const struct spasm_csr *A);

/* spasm_dm.c */
struct spasm_dm *spasm_dulmage_mendelsohn(const struct spasm_csr *A);

/* spasm_scc.c */
struct spasm_dm *spasm_strongly_connected_components(const struct spasm_csr *A);

/* spasm_ffpack.cpp */
int spasm_ffpack_rref(i64 prime, int n, int m, void *A, int ldA, spasm_datatype datatype, size_t *qinv);
int spasm_ffpack_LU(i64 prime, int n, int m, void *A, int ldA, spasm_datatype datatype, size_t *p, size_t *qinv);
spasm_ZZp spasm_datatype_read(const void *A, size_t i, spasm_datatype datatype);
void spasm_datatype_write(void *A, size_t i, spasm_datatype datatype, spasm_ZZp value);
size_t spasm_datatype_size(spasm_datatype datatype);
spasm_datatype spasm_datatype_choose(i64 prime);
const char * spasm_datatype_name(spasm_datatype datatype);

/* spasm_echelonize */
void spasm_echelonize_init_opts(struct echelonize_opts *opts);
struct spasm_lu* spasm_echelonize(const struct spasm_csr *A, struct echelonize_opts *opts);

/* spasm_rref.c */
struct spasm_csr * spasm_rref(const struct spasm_lu *fact, int *Rqinv);

/* spasm_kernel.c */
struct spasm_csr * spasm_kernel(const struct spasm_lu *fact);
struct spasm_csr * spasm_kernel_from_rref(const struct spasm_csr *R, const int *qinv);

/* spasm_solve.c */
bool spasm_solve(const struct spasm_lu *fact, const spasm_ZZp *b, spasm_ZZp *x);
struct spasm_csr * spasm_gesv(const struct spasm_lu *fact, const struct spasm_csr *B, bool *ok);

/* spasm_certificate.c */
struct spasm_rank_certificate * spasm_certificate_rank_create(const struct spasm_csr *A, const u8 *hash, const struct spasm_lu *fact);
bool spasm_certificate_rank_verify(const struct spasm_csr *A, const u8 *hash, const struct spasm_rank_certificate *proof);
void spasm_rank_certificate_save(const struct spasm_rank_certificate *proof, FILE *f);
bool spasm_rank_certificate_load(FILE *f, struct spasm_rank_certificate *proof);
bool spasm_factorization_verify(const struct spasm_csr *A, const struct spasm_lu *fact, u64 seed);


/* utilities */
static inline int spasm_max(int a, int b)
{
	return (a > b) ? a : b;
}

static inline int spasm_min(int a, int b)
{
	return (a < b) ? a : b;
}

static inline int spasm_row_weight(const struct spasm_csr * A, int i)
{
	i64 *Ap = A->p;
	return Ap[i + 1] - Ap[i];
}
#endif


// end of spasm.h

// start of spasm-master/src/spasm_reach.c

#include <assert.h>

/**
 * Depth-first-search along alternating paths of a bipartite graph.
 *
 * If a column j is pivotal (qinv[j] != -1), then move to the row (call it i)
 * containing the pivot; explore columns adjacent to row i, depth-first. 
 * The traversal starts at column jstart.
 *
 * qinv[j] indicates the row on which the j-th column pivot can be found.
 * qinv[j] == -1 means that there is no pivot on column j.
 *
 * xj is of size m (#columns). Used both as workspace and to return the result.
 * At the end, the list of traversed nodes is in xj[top:m].  This returns top.
 *
 * pstack : size-m workspace (used to count the neighbors already traversed)
 * marks  : size-m workspace (indicates which columns have been seen already)
 */
int spasm_dfs(int jstart, const struct spasm_csr *A, int top, int *xj, int *pstack, int *marks, const int *qinv)
{
	/* check inputs */
	assert(A != NULL);
	assert(xj != NULL);
	assert(pstack != NULL);
	assert(marks != NULL);
	assert(qinv != NULL);

	const i64 *Ap = A->p;
	const int *Aj = A->j;
	/*
	 * initialize the recursion stack (columns waiting to be traversed).
	 * The stack is held at the begining of xj, and has head elements.
	 */
	int head = 0;
	xj[head] = jstart;

	/* stack empty ? */
	while (head >= 0) {
		/* get j from the top of the recursion stack */
		int j = xj[head];
		int i = qinv[j];       /* row with the pivot on column j, or -1 if none */

		if (!marks[j]) {
			/* mark column j as seen and initialize pstack. This is done only once. */
			marks[j] = 1;
			pstack[head] = 0;
		}

		if (i < 0) {
			/* push initial column in the output stack and pop it from the recursion stack*/
			top -= 1;
			xj[top] = xj[head];
			head -= 1;
			continue;
		}

		/* size of row i */
		int p2 = spasm_row_weight(A, i);

		/* examine all yet-unseen entries of row i */
		int k;
		for (k = pstack[head]; k < p2; k++) {
			i64 px = Ap[i] + k;
			int j = Aj[px];
			if (marks[j])
				continue;
			/* interrupt the enumeration of entries of row i, and start DFS from column j */
			pstack[head] = k + 1;   /* Save status of row i in the stack. */
			xj[++head] = j;         /* push column j onto the recursion stack */
			break;
		}
		if (k == p2) {
			/* row i fully examined; push initial column in the output stack and pop it from the recursion stack */
			top -= 1;
			xj[top] = xj[head];
			head -= 1;
		}
	}
	return top;
}


/*
 * Reachability along alternating paths of a bipartite graph.
 * Compute the set of columns of A reachable from all columns indices in B[k]
 * (this is used to determine the pattern of a sparse triangular solve)
 * 
 * xj must be preallocated of size 3*m and zeroed out on entry.
 * On output, the set of reachable columns is in xj[top:m].
 * This returns top.  xj remains in a usable state (no need to zero it out again)
 *
 * qinv locates the pivots in A.
 *
 * This function does not require the pivots to be the first entries of the rows.
 */
int spasm_reach(const struct spasm_csr *A, const struct spasm_csr *B, int k, int l, int *xj, const int *qinv)
{
	/* check inputs */
	assert(A != NULL);
	assert(B != NULL);
	assert(xj != NULL);
	assert(qinv != NULL);

	const i64 *Bp = B->p;
	const int *Bj = B->j;
	int m = A->m;
	int top = m;
	int *pstack = xj + m;
	int *marks = pstack + m;

	/*
	 * iterates over the k-th row of B.  For each column index j present
	 * in B[k], check if j is in the pattern (i.e. if it is marked). If
	 * not, start a DFS from j and add to the pattern all columns
	 * reachable from j.
	 */
	for (i64 px = Bp[k]; px < Bp[k + 1]; px++) {
		int j = Bj[px];
		if (!marks[j])
			top = spasm_dfs(j, A, top, xj, pstack, marks, qinv);
	}

	/* unmark all marked nodes. */
	/*
	 * TODO : possible optimization : if stuff is marked "k", and
	 * initialized with -1, then this is not necessary
	 */
	for (int px = top; px < l; px++) {
		int j = xj[px];
		marks[j] = 0;
	}
	return top;
}


// end of spasm-master/src/spasm_reach.c
// start of spasm_ZZp.c

#include <assert.h>

void spasm_field_init(i64 p, spasm_field F)
{
	F->p = p;
	if (p < 0)
		return;
	assert(2 <= p);
	assert(p <= 0xfffffffbLL);
	F->halfp = p / 2;
	F->mhalfp = p / 2 - p + 1;
	F->dinvp = 1. / ((double) p);
}

static inline spasm_ZZp NORMALISE(const spasm_field F, i64 x)
{
	if (x < F->mhalfp)
		x += F->p;
	else if (x > F->halfp)
		x -= F->p;
	return x;
}

inline spasm_ZZp spasm_ZZp_init(const spasm_field F, i64 x)
{
	i64 p = F->p;
	return NORMALISE(F, x % p);
}

inline spasm_ZZp spasm_ZZp_add(const spasm_field F, spasm_ZZp a, spasm_ZZp b)
{
	return NORMALISE(F, (i64) a + (i64) b);
}

inline spasm_ZZp spasm_ZZp_sub(const spasm_field F, spasm_ZZp a, spasm_ZZp b)
{
	return NORMALISE(F, (i64) a - (i64) b);
}

inline spasm_ZZp spasm_ZZp_mul(const spasm_field F, spasm_ZZp a, spasm_ZZp b)
{
	i64 q = ((double) a) * ((double) b) * F->dinvp;
	return NORMALISE(F, (i64) a * (i64) b - q * F->p);
}

/* compute bezout relation u*a + v*p == 1; returns u */
static i64 gcdext(i64 a, i64 p)
{
	assert(a >= 0);
	i64 t = 0, u = 1;
	i64 r = p, s = a;
	while (s != 0) {
		i64 q = r / s;
		i64 foo = u;
		u = t - q * u;
		t = foo;

		i64 bar = s;
		s = r - q * s;
		r = bar;
	}
	return t;
}

spasm_ZZp spasm_ZZp_inverse(const spasm_field F, spasm_ZZp a)
{
	i64 aa = a;
	if (aa < 0)
		aa += F->p;
	i64 inva = gcdext(aa, F->p);
	return NORMALISE(F, inva);
}


inline spasm_ZZp spasm_ZZp_axpy(const spasm_field F, spasm_ZZp a, spasm_ZZp x, spasm_ZZp y)
{
	i64 q = (((((double) a) * ((double) x)) + (double) y) * F->dinvp);
	i64 aa = a;
	i64 xx = x;
	i64 yy = y;
	return NORMALISE(F, aa * xx + yy - q * F->p);
}

// end of spasm_ZZp.c

spasm_ZZp spasm_datatype_read(const void *A, size_t i, spasm_datatype datatype)
{
	switch (datatype) {	
	case SPASM_DOUBLE: return ((double *) A)[i];
	case SPASM_FLOAT: return ((float *) A)[i];
	case SPASM_I64: return ((i64 *) A)[i];
	}	
	assert(false);
}

void spasm_datatype_write(void *A, size_t i, spasm_datatype datatype, spasm_ZZp value)
{
	switch (datatype) {	
	case SPASM_DOUBLE: ((double *) A)[i] = value; return;
	case SPASM_FLOAT: ((float *) A)[i] = value; return;
	case SPASM_I64: ((i64 *) A)[i] = value; return;
	}	
	assert(false);
}

size_t spasm_datatype_size(spasm_datatype datatype)
{
	switch (datatype) {	
	case SPASM_DOUBLE: return sizeof(double);
	case SPASM_FLOAT: return sizeof(float);
	case SPASM_I64: return sizeof(i64);
	}	
	assert(false);	
}

spasm_datatype spasm_datatype_choose(i64 prime)
{
	// return SPASM_DOUBLE;
	if (prime <= 8191)
		return SPASM_FLOAT;
	else if (prime <= 189812531)
		return SPASM_DOUBLE;
	else
		return SPASM_I64;
}

const char * spasm_datatype_name(spasm_datatype datatype)
{
	switch (datatype) {	
	case SPASM_DOUBLE: return "double";
	case SPASM_FLOAT: return "float";
	case SPASM_I64: return "i64";
	}	
	assert(false);	
}

// start of spasm-master/src/spasm_util.c

#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <sys/time.h>
#include <err.h>
#include <inttypes.h>

int spasm_get_num_threads() {
#ifdef _OPENMP
	return omp_get_num_threads();
#else
	return 1;
#endif
}

int spasm_get_thread_num() {
#ifdef _OPENMP
	return omp_get_thread_num();
#else
	return 0;
#endif
}


double spasm_wtime()
{
	struct timeval ts;
	gettimeofday(&ts, NULL);
	return (double)ts.tv_sec + ts.tv_usec / 1E6;
}


i64 spasm_nnz(const struct spasm_csr * A)
{
	return A->p[A->n];
}

/* return a string representing n in 8 bytes */
void spasm_human_format(i64 n, char *target)
{
	if (n < 1000) {
		snprintf(target, 8, "%" PRId64, n);
		return;
	}
	if (n < 1000000) {
		snprintf(target, 8, "%.1fk", n / 1e3);
		return;
	}
	if (n < 1000000000) {
		snprintf(target, 8, "%.1fm", n / 1e6);
		return;
	}
	if (n < 1000000000000ll) {
		snprintf(target, 8, "%.1fg", n / 1e9);
		return;
	}
	if (n < 1000000000000000ll) {
		snprintf(target, 8, "%.1ft", n / 1e12);
		return;
	}
}

void *spasm_malloc(i64 size)
{
	void *x = malloc(size);
	if (x == NULL)
		err(1, "malloc failed (size %" PRId64 ")", size);
	return x;
}

void *spasm_calloc(i64 count, i64 size)
{
	void *x = calloc(count, size);
	if (x == NULL)
		err(1, "calloc failed");
	return x;
}

void *spasm_realloc(void *ptr, i64 size)
{
	void *x = realloc(ptr, size);
	if (ptr != NULL && x == NULL && size != 0)
		err(1, "realloc failed");
	return x;
}

/* allocate a sparse matrix (compressed-row form) */
struct spasm_csr *spasm_csr_alloc(int n, int m, i64 nzmax, i64 prime, bool with_values)
{
	struct spasm_csr *A = (struct spasm_csr *) spasm_malloc(sizeof(*A));
	spasm_field_init(prime, A->field);
	A->m = m;
	A->n = n;
	A->nzmax = nzmax;
	A->p = (i64*) spasm_malloc((n + 1) * sizeof(i64));
	A->j = (int *) spasm_malloc(nzmax * sizeof(int));
	A->x = with_values ? (spasm_ZZp *) spasm_malloc(nzmax * sizeof(spasm_ZZp)) : NULL;
	A->p[0] = 0;
	return A;
}

/* allocate a sparse matrix (triplet form) */
struct spasm_triplet *spasm_triplet_alloc(int n, int m, i64 nzmax, i64 prime, bool with_values)
{
	struct spasm_triplet *A = (struct spasm_triplet *) spasm_malloc(sizeof(*A));
	A->m = m;
	A->n = n;
	A->nzmax = nzmax;
	spasm_field_init(prime, A->field);
	A->nz = 0;
	A->i = (int *) spasm_malloc(nzmax * sizeof(int));
	A->j = (int *) spasm_malloc(nzmax * sizeof(int));
	A->x = with_values ? (spasm_ZZp *) spasm_malloc(nzmax * sizeof(spasm_ZZp)) : NULL;
	return A;
}

/*
 * change the max # of entries in a sparse matrix. If nzmax < 0, then the
 * matrix is trimmed to its current nnz.
 */
void spasm_csr_realloc(struct spasm_csr *A, i64 nzmax)
{
	if (nzmax < 0)
		nzmax = spasm_nnz(A);
	// if (spasm_nnz(A) > nzmax)
	// 	errx(1, "spasm_csr_realloc with too small nzmax (contains %" PRId64 " nz, asking nzmax=%" PRId64 ")", spasm_nnz(A), nzmax);
	A->j = (int *) spasm_realloc(A->j, nzmax * sizeof(int));
	if (A->x != NULL)
		A->x = (spasm_ZZp *) spasm_realloc(A->x, nzmax * sizeof(spasm_ZZp));
	A->nzmax = nzmax;
}

/*
 * change the max # of entries in a sparse matrix. If nzmax < 0, then the
 * matrix is trimmed to its current nnz.
 */
void spasm_triplet_realloc(struct spasm_triplet *A, i64 nzmax)
{
	if (nzmax < 0)
		nzmax = A->nz;
	// fprintf(stderr, "[realloc] nzmax=%ld. before %px %px %px\n", nzmax, A->i, A->j, A->x);
	A->i = (int *) spasm_realloc(A->i, nzmax * sizeof(int));
	A->j = (int *) spasm_realloc(A->j, nzmax * sizeof(int));
	if (A->x != NULL)
		A->x = (spasm_ZZp *) spasm_realloc(A->x, nzmax * sizeof(spasm_ZZp));
	// fprintf(stderr, "[realloc] after %px %px %px\n", A->i, A->j, A->x);
	A->nzmax = nzmax;
}

/* free a sparse matrix */
void spasm_csr_free(struct spasm_csr *A)
{
	if (A == NULL)
		return;
	free(A->p);
	free(A->j);
	free(A->x);		/* trick : free does nothing on NULL pointer */
	free(A);
}

void spasm_triplet_free(struct spasm_triplet *A)
{
	free(A->i);
	free(A->j);
	free(A->x);		/* trick : free does nothing on NULL pointer */
	free(A);
}

void spasm_csr_resize(struct spasm_csr *A, int n, int m)
{
	A->m = m;
	/* TODO: in case of a shrink, check that no entries are left outside */
	A->p = (i64 *) spasm_realloc(A->p, (n + 1) * sizeof(i64));
	if (A->n < n) {
		i64 *Ap = A->p;
		for (int i = A->n; i < n + 1; i++)
			Ap[i] = Ap[A->n];
	}
	A->n = n;
}

struct spasm_dm * spasm_dm_alloc(int n, int m)
{
	struct spasm_dm *P = (struct spasm_dm *) spasm_malloc(sizeof(*P));
	P->p = (int *) spasm_malloc(n * sizeof(int));
	P->q = (int *) spasm_malloc(m * sizeof(int));
	P->r = (int *) spasm_malloc((n + 6) * sizeof(int));
	P->c = (int *) spasm_malloc((m + 6) * sizeof(int));
	P->nb = 0;
	for (int i = 0; i < 5; i++) {
		P->rr[i] = 0;
		P->cc[i] = 0;
	}
	return P;
}

void spasm_dm_free(struct spasm_dm *P)
{
	free(P->p);
	free(P->q);
	free(P->r);
	free(P->c);
	free(P);
}

void spasm_lu_free(struct spasm_lu *N)
{
	free(N->qinv);
	free(N->p);
	spasm_csr_free(N->U);
	spasm_csr_free(N->L);
	free(N);
}

// end of spasm-master/src/spasm_util.c

// start of spasm_triplet.c

#include <assert.h>
#include <stdlib.h>


/* add an entry to a triplet matrix; enlarge it if necessary */
void spasm_add_entry(struct spasm_triplet *T, int i, int j, i64 x)
{
	assert((i >= 0) && (j >= 0));
	i64 px = T->nz;
	if (px == T->nzmax)
		spasm_triplet_realloc(T, 1 + 2 * T->nzmax);
	if (T->x != NULL) {
		spasm_ZZp xp = spasm_ZZp_init(T->field, x);
		if (xp == 0)
			return;
		T->x[px] = xp;
	}
	T->i[px] = i;
	T->j[px] = j;
	T->nz += 1;
	T->n = spasm_max(T->n, i + 1);
	T->m = spasm_max(T->m, j + 1);
}

void spasm_triplet_transpose(struct spasm_triplet *T)
{
	int *foo = T->i;
	T->i = T->j;
	T->j = foo;
	int bar = T->m;
	T->m = T->n;
	T->n = bar;
}

static void remove_explicit_zeroes(struct spasm_csr *A)
{
	int n = A->n;
	i64 *Ap = A->p;
	int *Aj = A->j;
	spasm_ZZp *Ax = A->x;
	if (Ax == NULL)
		return;
	i64 nz = 0;
	for (int i = 0; i < n; i++) {
		for (i64 it = Ap[i]; it < Ap[i + 1]; it++) {
			int j = Aj[it];
			spasm_ZZp x = Ax[it];
			if (x == 0)
				continue;
			Aj[nz] = j;
			Ax[nz] = x;
			nz += 1;
		}
		Ap[i + 1] = nz;
	}
	spasm_csr_realloc(A, -1);
}

/* in-place */
static void deduplicate(struct spasm_csr *A)
{
	int m = A->m;
	int n = A->n;
	i64 *Ap = A->p;
	int *Aj = A->j;
	spasm_ZZp *Ax = A->x;
	i64 *v = (i64 *) spasm_malloc(m * sizeof(*v));
	for (int j = 0; j < m; j++)
		v[j] = -1;

	i64 nz = 0;
	for (int i = 0; i < n; i++) {
		i64 p = nz;
		for (i64 it = Ap[i]; it < Ap[i + 1]; it++) {
			int j = Aj[it];
			assert(j < m);
			if (v[j] < p) { /* 1st entry on column j in this row */
				v[j] = nz;
				Aj[nz] = j;
				if (Ax)
					Ax[nz] = Ax[it];
				nz += 1;
			} else {
				if (Ax) { /* not the first one: sum them */
					i64 px = v[j];
					Ax[px] = spasm_ZZp_add(A->field, Ax[px], Ax[it]);
				}
			}
		}
		Ap[i] = p;
	}
	Ap[n] = nz;
	free(v);
	spasm_csr_realloc(A, -1);
}

/* C = compressed-row form of a triplet matrix T */
struct spasm_csr *spasm_compress(const struct spasm_triplet * T)
{
	int m = T->m;
	int n = T->n;
	i64 nz = T->nz;
	int *Ti = T->i;
	int *Tj = T->j;
	spasm_ZZp *Tx = T->x;
	
	double start = spasm_wtime();
	fprintf(stderr, "[CSR] Compressing... ");
	fflush(stderr);

	/* allocate result */
	struct spasm_csr *C = spasm_csr_alloc(n, m, nz, T->field->p, Tx != NULL);

	/* get workspace */
	i64 *w = (i64 *) spasm_malloc(n * sizeof(*w));
	for (int i = 0; i < n; i++)
		w[i] = 0;
	i64 *Cp = C->p;
	int *Cj = C->j;
	spasm_ZZp *Cx = C->x;

	/* compute row counts */
	for (int it = 0; it < nz; it++) {
		int i = Ti[it];
		assert(i < n);
		w[i] += 1;
	}

	/* compute row pointers (in both Cp and w) */
	i64 sum = 0;
	for (int k = 0; k < n; k++) {
		Cp[k] = sum;
		sum += w[k];
		w[k] = Cp[k];
	}
	Cp[n] = sum;

	/* dispatch entries */
	for (i64 k = 0; k < nz; k++) {
		int i = Ti[k];
		i64 px = w[i];
		w[i] += 1;
		Cj[px] = Tj[k];
		if (Cx != NULL)
			Cx[px] = Tx[k];
	}
	free(w);
	deduplicate(C);
	remove_explicit_zeroes(C);

	/* success; free w and return C */
	char mem[16];
	int size = sizeof(int) * (n + nz) + sizeof(spasm_ZZp) * ((Cx != NULL) ? nz : 0);
	spasm_human_format(size, mem);
	fprintf(stderr, "%" PRId64 " actual NZ, Mem usage = %sbyte [%.2fs]\n", spasm_nnz(C), mem, spasm_wtime() - start);
	return C;
}

// end of spasm_triplet.c

// start of spasm-master/src/spasm_echelonize.c
#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <math.h>


/* provide sensible defaults */
void spasm_echelonize_init_opts(struct echelonize_opts *opts)
{
	opts->enable_greedy_pivot_search = 1;
	
	opts->enable_tall_and_skinny = 1;
	opts->enable_dense = 1;
	opts->enable_GPLU = 1;

	// options of the main procedure
	opts->L = 0;
	opts->complete = 0;
	opts->min_pivot_proportion = 0.1;
	opts->max_round = 3;
	opts->sparsity_threshold = 0.05;
	opts->tall_and_skinny_ratio = 5;

	opts->dense_block_size = 1000;
	opts->low_rank_ratio = 0.5;
	opts->low_rank_start_weight = -1;
}

// bool spasm_echelonize_test_completion(const struct spasm_csr *A, const int *p, int n, struct spasm_csr *U, int *Uqinv)
// {
// 	/* deal with the easy cases first */
// 	if (n == 0 || spasm_nnz(A) == 0)
// 		return 1;
// 	int m = A->m;
// 	i64 Sm = m - U->n;
// 	i64 prime = spasm_get_prime(A);
// 	spasm_datatype datatype = spasm_datatype_choose(prime);
// 	i64 Sn = ceil(128 / log2(prime));
// 	void *S = spasm_malloc(Sn * Sm * spasm_datatype_size(datatype));
// 	int *q = (int *) spasm_malloc(Sm * sizeof(*q));
// 	size_t *Sp = (size_t *) spasm_malloc(Sm * sizeof(*Sp));       /* for FFPACK */
// 	fprintf(stderr, "[echelonize/completion] Testing completion with %" PRId64" random linear combinations (rank %d)\n", Sn, U->n);
// 	fflush(stderr);
// 	spasm_schur_dense_randomized(A, p, n, U, Uqinv, S, datatype, q, Sn, 0);
// 	int rr = spasm_ffpack_rref(prime, Sn, Sm, S, Sm, datatype, Sp);
// 	free(S);
// 	free(Sp);
// 	free(q);
// 	return (rr == 0);
// }


static void echelonize_GPLU(const struct spasm_csr *A, const int *p, int n, const int *p_in, struct spasm_lu *fact, struct echelonize_opts *opts)
{
	(void) opts;
	assert(p != NULL);
	int m = A->m;
	int r = spasm_min(A->n, m);  /* upper-bound on rank */
	int verbose_step = spasm_max(1, n / 1000);
	fprintf(stderr, "[echelonize/GPLU] processing matrix of dimension %d x %d\n", n, m);
	
	struct spasm_csr *U = fact->U;
	struct spasm_triplet *L = fact->Ltmp;
	int *Uqinv = fact->qinv;
	i64 *Up = U->p;
	i64 unz = spasm_nnz(U);
	i64 lnz = (L != NULL) ? L->nz : 0;
	int *Lp = fact->p;

	/* initialize early abort */
	int rows_since_last_pivot = 0;
	bool early_abort_done = 0;

	/* workspace for triangular solver */
	spasm_ZZp *x = (spasm_ZZp *) spasm_malloc(m * sizeof(*x));
	int *xj = (int *) spasm_malloc(3 * m * sizeof(*xj));
	for (int j = 0; j < 3*m; j++)
		xj[j] = 0;

	/* Main loop : compute L[i] and U[i] */
	int i;
	for (i = 0; i < n; i++) {
		/* test for early abort (if L not needed) */
		// if (L == NULL && U->n == r) {
		// 	fprintf(stderr, "\n[echelonize/GPLU] full rank reached\n");
		// 	break;
		// }
		// /* TODO: make these hard-coded values options */
		// if (L == NULL && !early_abort_done && rows_since_last_pivot > 10 && (rows_since_last_pivot > (n / 100))) {
		// 	fprintf(stderr, "\n[echelonize/GPLU] testing for early abort...\n");
		// 	// if (spasm_echelonize_test_completion(A, p, n, U, Uqinv))
		// 	// 	break;
		// 	early_abort_done = 1;
		// }
		rows_since_last_pivot += 1;

		/* ensure enough room in L / U for an extra row */
		if (unz + m > U->nzmax)
			spasm_csr_realloc(U, 2 * U->nzmax + m);
		int *Uj = U->j;
		spasm_ZZp *Ux = U->x;
		if (L && lnz + m > L->nzmax)
			spasm_triplet_realloc(L, 2 * L->nzmax + m);
		int *Li = (L != NULL) ? L->i : NULL;
		int *Lj = (L != NULL) ? L->j : NULL;
		spasm_ZZp *Lx = (L != NULL) ? L->x : NULL;

		/* Triangular solve: x * U = A[i] */
		int inew = p[i];
		int i_orig = (p_in != NULL) ? p_in[inew] : inew;
		int top = spasm_sparse_triangular_solve(U, A, inew, xj, x, Uqinv);

		/* Find pivot column; current poor strategy= choose leftmost */
		int jpiv = m ;                 /* column index of best pivot so far. */
		for (int px = top; px < m; px++) {
			int j = xj[px];        /* x[j] is (generically) nonzero */
			if (x[j] == 0)
				continue;
			if (Uqinv[j] < 0) {
				/* non-zero coeff on non-pivotal column --> candidate */
				if (j < jpiv)
					jpiv = j;
			} else if (L != NULL) {
				/* everything under pivotal columns goes into L */
				Li[lnz] = i_orig;
				Lj[lnz] = Uqinv[j];
				Lx[lnz] = x[j];
				lnz += 1;
			}	
		}
		
		if (jpiv == m)
			continue;        /* no pivot found */

		/* add entry entry in L for the pivot */
		if (L != NULL) {
			assert(x[jpiv] != 0);
			Lp[U->n] = i_orig;
			Li[lnz] = i_orig;
			Lj[lnz] = U->n;
			Lx[lnz] = x[jpiv];
			lnz += 1;
		}

		/* store new pivotal row into U */
		Uqinv[jpiv] = U->n;
		// fprintf(stderr, "setting Uqinv[%d] <--- %d\n", jpiv, U->n);

		i64 old_unz = unz;
		Uj[unz] = jpiv;
		Ux[unz] = 1;
		unz += 1;
		// fprintf(stderr, "setting U[%d, %d] <--- 1\n", U->n, jpiv);
		assert(x[jpiv] != 0);
		spasm_ZZp beta = spasm_ZZp_inverse(A->field, x[jpiv]);
		for (int px = top; px < m; px++) {
			int j = xj[px];
			if (x[j] != 0 && Uqinv[j] < 0) {
				Uj[unz] = j;
				Ux[unz] = spasm_ZZp_mul(A->field, beta, x[j]);
				// fprintf(stderr, "setting U[%d, %d] <--- %d\n", U->n, j, Ux[unz]);
				unz += 1;
			}
		}
		U->n += 1;
		Up[U->n] = unz;

		/* reset early abort */
		rows_since_last_pivot = 0;
		early_abort_done = 0;

		if ((i % verbose_step) == 0) {
			fprintf(stderr, "\r[echelonize/GPLU] %d / %d [|U| = %" PRId64 " / |L| = %" PRId64"] -- current density= (%.3f vs %.3f) --- rank >= %d", 
				i, n, unz, lnz, 1.0 * (m - top) / (m), 1.0 * (unz - old_unz) / m, U->n);
			fflush(stderr);
		}
	}
	/* cleanup */
	if (L) {
		L->nz = lnz;
		L->m = U->n;
	}
	fprintf(stderr, "\n");
	free(x);
	free(xj);
}

/*
 * Transfer echelonized rows from (dense) S to (sparse) U
 */
static void update_U_after_rref(int rr, int Sm, const void *S, spasm_datatype datatype, 
	const size_t *Sqinv, const int *q, struct spasm_lu *fact)
{
	struct spasm_csr *U = fact->U;
	int *Uqinv = fact->qinv;
	i64 extra_nnz = ((i64) (1 + Sm - rr)) * rr;     /* maximum size increase */
	i64 unz = spasm_nnz(U);
	fprintf(stderr, "[dense update] enlarging U from %" PRId64 " to %" PRId64 " entries\n", unz, unz + extra_nnz);
	spasm_csr_realloc(U, unz + extra_nnz);
	i64 *Up = U->p;
	int *Uj = U->j;
	spasm_ZZp *Ux = U->x;
	for (i64 i = 0; i < rr; i++) {
		int j = Sqinv[i];   /* column (of S) with the pivot on row i of S; the pivot is implicitly 1 */
		Uj[unz] = q[j];  /* column of A with the pivot */
		Ux[unz] = 1;
		unz += 1;
		Uqinv[q[j]] = U->n;
		for (i64 k = rr; k < Sm; k++) {
			i64 j = Sqinv[k];
			spasm_ZZp x = spasm_datatype_read(S, i * Sm + k, datatype);
			if (x == 0)
				continue;   /* don't store zero */
			Uj[unz] = q[j];
			Ux[unz] = x;  // reduce?
			unz += 1;
		}
		U->n += 1;
		Up[U->n] = unz;
	}
	assert(unz == spasm_nnz(U));
}

/*
 * Transfer dense LU factorization to fact
 */
static void update_fact_after_LU(int n, int Sm, int r, const void *S, spasm_datatype datatype, 
	const size_t *Sp, const size_t *Sqinv, const int *q, const int *p_in, i64 lnz_before, 
	bool complete, bool *pivotal, struct spasm_lu *fact)
{
	struct spasm_csr *U = fact->U;
	struct spasm_triplet *L = fact->Ltmp;
	int *Uqinv = fact->qinv;
	int *Lp = fact->p;
	i64 extra_unz = ((i64) (1 + 2*Sm - r)) * r;     /* maximum size increase */
	i64 extra_lnz = ((i64) (2*n - r + 1)) * r / 2;
	i64 unz = spasm_nnz(U);
	i64 lnz = L->nz;
	spasm_csr_realloc(U, unz + extra_unz);
	spasm_triplet_realloc(L, lnz + extra_lnz);
	i64 *Up = U->p;
	int *Uj = U->j;
	spasm_ZZp *Ux = U->x;
	int *Li = L->i;
	int *Lj = L->j;
	spasm_ZZp *Lx = L->x;
	
	/* build L */
	if (!complete) {
		for (i64 i = 0; i < r; i++) {   /* mark pivotal rows */
			int pi = Sp[i];
			int iorig = (p_in != NULL) ? p_in[pi] : pi;
			pivotal[iorig] = 1;
		}

		/* stack L (ignore non-pivotal rows) */
		lnz = lnz_before;
		for (i64 px = lnz_before; px < L->nz; px++) {
			int i = Li[px];
			if (!pivotal[i])
				continue;
			int j = Lj[px];
			spasm_ZZp x = Lx[px];
			Li[lnz] = i;
			Lj[lnz] = j;
			Lx[lnz] = x;
			lnz += 1;
		}
		fprintf(stderr, "L : %" PRId64 " --> %" PRId64 " --> %" PRId64 " ---> ", lnz_before, L->nz, lnz);
	}

	/* add new entries from S */
	for (i64 i = 0; i < (complete ? n : r); i++) {
		int pi = Sp[i];
		int iorig = (p_in != NULL) ? p_in[pi] : pi;
		for (i64 j = 0; j < spasm_min(i + 1, r); j++) {
			spasm_ZZp Mij = spasm_datatype_read(S, i  * Sm + j, datatype);
			if (Mij == 0)
				continue;
			Li[lnz] = iorig;
			Lj[lnz] = U->n + j;
			Lx[lnz] = Mij;
			lnz += 1;
		}
		if (i < r)   /* register pivot */
			Lp[U->n + i] = iorig;
	}
	L->nz = lnz;
	fprintf(stderr, "%" PRId64 "\n", lnz);

	/* fill U */
	for (i64 i = 0; i < r; i++) {
		/* implicit 1 in U */
		int j = Sqinv[i];
		int jorig = q[j];
		Uj[unz] = jorig;
		Ux[unz] = 1;
		unz += 1;
		/* register pivot */
		Uqinv[jorig] = U->n;
		for (i64 j = i+1; j < Sm; j++) {
			int jnew = Sqinv[j];
			int jorig = q[jnew];
			spasm_ZZp x = spasm_datatype_read(S, i * Sm + j, datatype);
			Uj[unz] = jorig;
			Ux[unz] = x;
			unz += 1;
		}
		U->n += 1;
		Up[U->n] = unz;
	}
}

// static void echelonize_dense_lowrank(const struct spasm_csr *A, const int *p, int n, struct spasm_lu *fact, struct echelonize_opts *opts)
// {
// 	assert(opts->dense_block_size > 0);
// 	struct spasm_csr *U = fact->U;
// 	int *Uqinv = fact->qinv;
// 	int m = A->m;
// 	int Sm = m - U->n;
// 	i64 prime = spasm_get_prime(A);
// 	spasm_datatype datatype = spasm_datatype_choose(prime);

// 	i64 size_S = (i64) opts->dense_block_size * (i64) Sm * spasm_datatype_size(datatype);
// 	void *S = spasm_malloc(size_S);
// 	int *q = (int *) spasm_malloc(Sm * sizeof(*q));
// 	size_t *Sp = (size_t *) spasm_malloc(Sm * sizeof(*Sp));       /* for FFPACK */
// 	double start = spasm_wtime();
// 	int old_un = U->n;
// 	int round = 0;
// 	fprintf(stderr, "[echelonize/dense/low-rank] processing dense schur complement of dimension %d x %d; block size=%d, type %s\n", 
// 		n, Sm, opts->dense_block_size, spasm_datatype_name(datatype));
	
// 	/* 
// 	 * stupid algorithm to decide a starting weight:
// 	 * - estimate the number of passes as rank_ub / opts->dense_block_size
// 	 * - thus rank_ub * w rows are selected in total
// 	 * - a single row is never selected with proba (1 - 1/n) ** (rank_ub * w)
// 	 * - choose w such that this is less than 0.01
// 	 * - this leads to w >= log 0.01 / log (1 - 1/n) / rank_ub
// 	 * - this is approximately w >= log 0.01 * n / rank_ub
// 	 */
// 	int rank_ub = spasm_min(n, Sm);
// 	int w = (opts->low_rank_start_weight < 0) ? ceil(-log(0.01) * n / rank_ub) : opts->low_rank_start_weight;

// 	for (;;) {
// 		/* compute a chunk of the schur complement, then echelonize with FFPACK */
// 		int Sn = spasm_min(rank_ub, opts->dense_block_size);
// 		if (Sn <= 0)
// 			break;		
// 		// fprintf(stderr, "[echelonize/dense/low-rank] Round %d. Weight %d. Processing chunk (%d x %d), |U| = %"PRId64"\n", 
// 		// 	round, w, Sn, Sm, spasm_nnz(U));
// 		spasm_schur_dense_randomized(A, p, n, U, Uqinv, S, datatype, q, Sn, w);
// 		int rr = spasm_ffpack_rref(prime, Sn, Sm, S, Sm, datatype, Sp);

// 		if (rr == 0) {
// 			if (spasm_echelonize_test_completion(A, p, n, U, Uqinv))
// 				break;
// 			fprintf(stderr, "[echelonize/dense/low-rank] Failed termination test; switching to full linear combinations\n");
// 			w = 0;
// 			Sn = omp_get_max_threads();
// 		}
// 		if (rr < 0.9 * Sn) {
// 			w *= 2;
// 			fprintf(stderr, "[echelonize/dense/low-rank] Not enough pivots, increasing weight to %d\n", w);
// 		}
// 		update_U_after_rref(rr, Sm, S, datatype, Sp, q, fact);
// 		n -= rr;
// 		Sm -= rr;
// 		rank_ub -= rr;
// 		round += 1;
// 		fprintf(stderr, "[echelonize/dense/low-rank] found %d new pivots (%d new since beginning)\n", rr,  U->n - old_un);
// 	}
// 	fprintf(stderr, "[echelonize/dense/low-rank] completed in %.1fs. %d new pivots found\n", spasm_wtime() - start, U->n - old_un);
// 	free(S);
// 	free(q);
// 	free(Sp);
// }

/* 
 * the schur complement (on non-pivotal rows of A) w.r.t. U is dense.
 * process (P*A)[0:n]
 */
// static void echelonize_dense(const struct spasm_csr *A, const int *p, int n, const int *p_in, struct spasm_lu *fact, struct echelonize_opts *opts)
// {
// 	assert(opts->dense_block_size > 0);
// 	struct spasm_csr *U = fact->U;
// 	int m = A->m;
// 	int Sm = m - U->n;
// 	i64 prime = spasm_get_prime(A);
// 	spasm_datatype datatype = spasm_datatype_choose(prime);

// 	void *S = spasm_malloc((i64) opts->dense_block_size * Sm * spasm_datatype_size(datatype));
// 	int *p_out = (int *) spasm_malloc(opts->dense_block_size * sizeof(*p_out));
// 	int *q = (int *) spasm_malloc(Sm * sizeof(*q));
// 	size_t *Sqinv = (size_t *) spasm_malloc(Sm * sizeof(*Sqinv));                   /* for FFPACK */
// 	size_t *Sp = (size_t *) spasm_malloc(opts->dense_block_size * sizeof(*Sp));     /* for FFPACK / LU only */
// 	bool *pivotal = (bool *) spasm_malloc(A->n * sizeof(*pivotal));
// 	for (int i = 0; i < A->n; i++)
// 		pivotal[i] = 0;

// 	int processed = 0;
// 	double start = spasm_wtime();
// 	int old_un = U->n;
// 	int round = 0;
// 	// fprintf(stderr, "[echelonize/dense] processing dense schur complement of dimension %d x %d; block size=%d, type %s\n", 
// 	// 	n, Sm, opts->dense_block_size, spasm_datatype_name(datatype));
// 	bool lowrank_mode = 0;
// 	int rank_ub = spasm_min(A->n - U->n, A->m - U->n);

// 	for (;;) {
// 		/* compute a chunk of the schur complement, then echelonize with FFPACK */
// 		int Sn = spasm_min(opts->dense_block_size, n - processed);
// 		if (Sn <= 0)
// 			break;
		
// 		fprintf(stderr, "[echelonize/dense] Round %d. processing S[%d:%d] (%d x %d)\n", round, processed, processed + Sn, Sn, Sm);	

// 		i64 lnz_before = (opts->L) ? fact->Ltmp->nz : -1;
// 		spasm_schur_dense(A, p, Sn, p_in, fact, S, datatype, q, p_out);

// 		int rr;
// 		if (opts->L) {
// 			rr = spasm_ffpack_LU(prime, Sn, Sm, S, Sm, datatype, Sp, Sqinv);
// 			update_fact_after_LU(Sn, Sm, rr, S, datatype, Sp, Sqinv, q, p_out, lnz_before, opts->complete, pivotal, fact);
// 		} else {
// 			rr = spasm_ffpack_rref(prime, Sn, Sm, S, Sm, datatype, Sqinv);
// 			update_U_after_rref(rr, Sm, S, datatype, Sqinv, q, fact);
// 		}

// 		// TODO: test completion and allow early abort

// 		/* move on to the next chunk */
// 		round += 1;
// 		processed += Sn;
// 		p += Sn;
// 		Sm = m - U->n;
// 		rank_ub = spasm_min(A->n - U->n, A->m - U->n);
// 		fprintf(stderr, "[echelonize/dense] found %d new pivots\n", rr);

// 		/* 
// 		 * switch to low-rank mode if yield drops too much 
// 		 * This will early abort if a full factorization is not needed
// 		 */
// 		if (opts->enable_tall_and_skinny && (rr < opts->low_rank_ratio * Sn)) {
// 			lowrank_mode = 1;
// 			break;
// 		}
// 	}
// 	free(S);
// 	free(q);
// 	free(Sqinv);
// 	free(Sp);
// 	free(p_out);
// 	free(pivotal);
// 	if (rank_ub > 0 && n - processed > 0 && lowrank_mode) {
// 		fprintf(stderr, "[echelonize/dense] Too few pivots; switching to low-rank mode\n");
// 		echelonize_dense_lowrank(A, p, n - processed, fact, opts);
// 	} else {
// 		fprintf(stderr, "[echelonize/dense] completed in %.1fs. %d new pivots found\n", spasm_wtime() - start, U->n - old_un);
// 	}
// }


/*
 * (main entry point)
 * Returns the row echelon form of A. 
 * Initializes Uqinv (must be preallocated of size m [==#columns of A]).
 * Modifies A (permutes entries in rows)
 * FIXME potential memleak (>= 1 rounds then status == 1...)
 */
struct spasm_lu * spasm_echelonize(const struct spasm_csr *A, struct echelonize_opts *opts)
{
	struct echelonize_opts default_opts;
	if (opts == NULL) {
		fprintf(stderr, "[echelonize] using default settings\n");
		opts = &default_opts;
		spasm_echelonize_init_opts(opts);
	}
	int n = A->n;
	int m = A->m;
	i64 prime = spasm_get_prime(A);
	fprintf(stderr, "[echelonize] Start on %d x %d matrix with %" PRId64 " nnz\n", n, m, spasm_nnz(A));
	
	/* options sanity check */
	if (opts->complete)
		opts->L = 1;
	if (opts->L)
		opts->enable_tall_and_skinny = 0;   // for now

	/* allocate result */
	struct spasm_csr *U = spasm_csr_alloc(n, m, spasm_nnz(A), prime, true);
	int *Uqinv = (int *) spasm_malloc(m * sizeof(*Uqinv));
	U->n = 0;
	for (int j = 0; j < m; j++)
		Uqinv[j] = -1;
	
	struct spasm_triplet *L = NULL;
	int *Lp = NULL;
	if (opts->L) {
		L = spasm_triplet_alloc(n, n, spasm_nnz(A), prime, true);
		Lp = (int *) spasm_malloc(n * sizeof(*Lp));
		for (int j = 0; j < n; j++)
			Lp[j] = -1;
		assert(L->x != NULL);
	}
	
	struct spasm_lu *fact = (struct spasm_lu *) spasm_malloc(sizeof(*fact));
	fact->L = NULL;
	fact->p = Lp;
	fact->U = U;
	fact->qinv = Uqinv;
	fact->Ltmp = L;

	/* local stuff */
	int *p = (int *) spasm_malloc(n * sizeof(*p)); /* pivotal rows come first in P*A */
	double start = spasm_wtime();
	double density = (double) spasm_nnz(A) / n / m;
	int npiv = 0;
	int status = 0;  /* 0 == max_round reached; 1 == full rank reached; 2 == early abort */
	int *p_in = NULL;

	int round;
	for (round = 0; round < opts->max_round; round++) {
		/* decide whether to move on to the next iteration */
		if (spasm_nnz(A) == 0) {
			fprintf(stderr, "[echelonize] empty matrix\n");
			status = 1;
			break;
		}
		
		fprintf(stderr, "[echelonize] round %d\n", round);
		npiv = spasm_pivots_extract_structural(A, p_in, fact, p, opts);

		if (npiv < opts->min_pivot_proportion * spasm_min(n, m - U->n)) {
			fprintf(stderr, "[echelonize] not enough pivots found; stopping\n");
			status = 2;
			break;     /* not enough pivots found */
		}		
		// if (density > opts->sparsity_threshold && aspect_ratio > opts->tall_and_skinny_ratio) {
		// 	fprintf(stderr, "Schur complement is dense, tall and skinny (#rows / #cols = %.1f)\n", aspect_ratio);
		// 	break;
		// }
		density = spasm_schur_estimate_density(A, p + npiv, n - npiv, U, Uqinv, 100);
		if (density > opts->sparsity_threshold) {
			fprintf(stderr, "[echelonize] Schur complement is dense (estimated %.2f%%)\n", 100 * density);
			status = 2;
			break;
		}

		/* compute the next schur complement */
		i64 nnz = (density * (n - npiv)) * (m - U->n);
		char tmp[8];
		spasm_human_format(sizeof(int) * (n - npiv + nnz) + sizeof(spasm_ZZp) * nnz, tmp);
		fprintf(stderr, "Schur complement is %d x %d, estimated density : %.2f (%s byte)\n", n - npiv, m - U->n, density, tmp);
		int *p_out = (int *) spasm_malloc((n - npiv) * sizeof(*p_out));
		struct spasm_csr *S = spasm_schur(A, p + npiv, n - npiv, fact, density, L, p_in, p_out);
		if (round > 0)
			spasm_csr_free((struct spasm_csr *) A);       /* discard const, only if it is not the input argument */
		A = S;
		n = n - npiv;
		free(p_in);
		p_in = p_out;
	}
	/*
	 * status == 0. Exit because opts->max_round reached. Just factor A.
	 * status == 1. Exit because A == 0. Nothing more to do.
	 * status == 2. Some pivots found (U/L updated), but schur complement not computed (too few pivots / too dense).
	 */

	if (status == 0) {
		npiv = 0;
		for (int i = 0; i < n; i++)
			p[i] = i;
	}
	if (status != 1)
	{

	/* finish */
	if (!opts->enable_tall_and_skinny)
		fprintf(stderr, "[echelonize] dense low-rank mode disabled\n");
	if (!opts->enable_dense)
		fprintf(stderr, "[echelonize] regular dense mode disabled\n");
	if (!opts->enable_GPLU)
		fprintf(stderr, "[echelonize] GPLU mode disabled\n");
	
	double aspect_ratio = (double) (n - npiv) / (m - U->n);
	fprintf(stderr, "[echelonize] finishing; density = %.3f; aspect ratio = %.1f\n", density, aspect_ratio);
	// if (opts->enable_tall_and_skinny && aspect_ratio > opts->tall_and_skinny_ratio)
	// {}
	// 	// echelonize_dense_lowrank(A, p + npiv, n - npiv, fact, opts);
	// else if (opts->enable_dense && density > opts->sparsity_threshold)
	// {}
	// 	// echelonize_dense(A, p + npiv, n - npiv, p_in, fact, opts);
	// else if (opts->enable_GPLU)
    
	if (opts->enable_GPLU)
	{
		printf("GPLU\n");
		echelonize_GPLU(A, p + npiv, n - npiv, p_in, fact, opts);
	}
	else
		fprintf(stderr, "[echelonize] Cannot finish (no valid method enabled). Incomplete echelonization returned\n");
	}

	free(p);
	free(p_in);
	fprintf(stderr, "[echelonize] Done in %.1fs. Rank %d, %" PRId64 " nz in basis\n", spasm_wtime() - start, U->n, spasm_nnz(U));
	spasm_csr_resize(U, U->n, m);
	spasm_csr_realloc(U, -1);
	if (round > 0)
		spasm_csr_free((struct spasm_csr *) A);
	if (opts->L) {
		L->m = U->n; 
		fact->p = (int *) spasm_realloc(Lp, U->n * sizeof(*Lp));
		fact->L = spasm_compress(L);
		spasm_triplet_free(L);
		fact->Ltmp = NULL;
		fact->complete = opts->complete;
	}
	fact->r = U->n;
	return fact;
}

// end of spasm-master/src/spasm_echelonize.c

// start of spasm_schur.c

#include <stdlib.h>
#include <assert.h>
#include <err.h>


/*
 * Samples R rows at random in the schur complement of (P*A)[0:n] w.r.t. U, and return the average density.
 * qinv locates the pivots in U.
 */
double spasm_schur_estimate_density(const struct spasm_csr *A, const int *p, int n, const struct spasm_csr *U, const int *qinv, int R)
{
	if (n == 0)
		return 0;
	int m = A->m;
	i64 nnz = 0;
	if (n == 0)
		return 0;

	#pragma omp parallel
	{
		/* per-thread scratch space */
		spasm_ZZp *x = (spasm_ZZp *) spasm_malloc(m * sizeof(*x));
		int *xj = (int *) spasm_malloc(3 * m * sizeof(*xj));
		for (int j = 0; j < 3 * m; j++)
			xj[j] = 0;

		#pragma omp for reduction(+:nnz) schedule(dynamic)
		for (int i = 0; i < R; i++) {
			/* pick a random non-pivotal row in A */
			int inew = p[rand() % n];
			int top = spasm_sparse_triangular_solve(U, A, inew, xj, x, qinv);
			for (int px = top; px < m; px++) {
				int j = xj[px];
				if ((qinv[j] < 0) && (x[j] != 0))
					nnz += 1;
			}
		}

		free(x);
		free(xj);
	}
	return ((double) nnz) / (m - U->n) / R;
}

/*
 * Computes the Schur complement of (P*A)[0:n] w.r.t. U
 * The pivots need not be the first entries on the rows.
 * The pivots must be unitary.	
 * This returns a sparse representation of S. 
 *
 * qinv describes the location of pivots in U. qinv[j] == i --> pivot on col j is on row i / -1 if none)
 * note that it is possible to have U == A.
 *
 * if L is not NULL, then the corresponding entries will be added
 * It is understood that row i of A corresponds to row p_in[i] of the original matrix.
 * if p_out is not NULL, then row i of the output corresponds to row p_out[i] of the original matrix.
 *
 * If the estimated density is unknown, set it to -1: it will be evaluated
 */
struct spasm_csr *spasm_schur(const struct spasm_csr *A, const int *p, int n, const struct spasm_lu *fact, 
	double est_density, struct spasm_triplet *L, const int *p_in, int *p_out)
{
	assert(p != NULL);

	int m = A->m;
	const int *qinv = fact->qinv;
	int verbose_step = spasm_max(1, n / 1000);
	if (est_density < 0)
		est_density = spasm_schur_estimate_density(A, p, n, fact->U, qinv, 100);
	long long size = (est_density * n) * m;
	i64 prime = spasm_get_prime(A);
	struct spasm_csr *S = spasm_csr_alloc(n, m, size, prime, true);
	i64 *Sp = S->p;
	int *Sj = S->j;
	spasm_ZZp *Sx = S->x;
	i64 snz = 0;                               /* nnz in S at the moment */
	int Sn = 0;                                /* #rows in S at the moment */
	i64 lnz = (L != NULL) ? L->nz : 0;         /* nnz in L at the moment */
	int *Li = (L != NULL) ? L->i : NULL;
	int *Lj = (L != NULL) ? L->j : NULL;
	spasm_ZZp *Lx = (L != NULL) ? L->x : NULL;
	int writing = 0;
	double start = spasm_wtime();

	#pragma omp parallel
	{
		/* scratch space for the triangular solver */
		spasm_ZZp *x = (spasm_ZZp *) spasm_malloc(m * sizeof(*x));
		int *xj = (int *) spasm_malloc(3 * m * sizeof(*xj));
		for (int j = 0; j < 3 * m; j++)
			xj[j] = 0;
		int tid = spasm_get_thread_num();

		#pragma omp for schedule(dynamic, verbose_step)
		for (int i = 0; i < n; i++) {
			int inew = p[i];
			int top = spasm_sparse_triangular_solve(fact->U, A, inew, xj, x, qinv);

			int row_snz = 0;             /* #nz coefficients in the row of S */
			int row_lnz = 0;             /* #nz coefficients in the row of L */
			for (int px = top; px < m; px++) {
				int j = xj[px];
				if (x[j] == 0)
					continue;
				if (qinv[j] < 0)
					row_snz += 1;
				else
					row_lnz += 1;
			}

			int local_i;
			i64 local_snz, local_lnz;
			#pragma omp critical(schur_complement)
			{
				/* enough room in S? */
				if (snz + row_snz > S->nzmax) {
					/* wait until other threads stop writing into it */
					#pragma omp flush(writing)
					while (writing > 0) {
						#pragma omp flush(writing)
					}
					spasm_csr_realloc(S, 2 * S->nzmax + m);
					Sj = S->j;
					Sx = S->x;
				}
				/* save row Sn */
				local_i = Sn;
				Sn += 1;
				local_snz = snz;
				snz += row_snz;

				if (L != NULL && lnz + row_lnz > L->nzmax) {
					/* wait until other threads stop writing into it */
					#pragma omp flush(writing)
					while (writing > 0) {
						#pragma omp flush(writing)
					}
					spasm_triplet_realloc(L, 2 * L->nzmax + m);
					Li = L->i;
					Lj = L->j;
					Lx = L->x;
				}
				local_lnz = lnz;
				lnz += row_lnz;

				#pragma omp atomic update
				writing += 1;    /* register as a writing thread */
			}
			
			/* write the new row in L / S */
			int i_orig = (p_in != NULL) ? p_in[inew] : inew;
			if (p_out != NULL)
				p_out[local_i] = i_orig;

			for (int px = top; px < m; px++) {
				int j = xj[px];
				if (x[j] == 0)
					continue;
				if (qinv[j] < 0) {
					Sj[local_snz] = j;
					Sx[local_snz] = x[j];
					local_snz += 1;
				} else if (L != NULL) {
					Li[local_lnz] = i_orig;
					Lj[local_lnz] = qinv[j];
					Lx[local_lnz] = x[j];
					// fprintf(stderr, "Adding L[%d, %d] = %d\n", i_out, qinv[j], x[j]);
					local_lnz += 1;
				}
			}
			Sp[local_i + 1] = local_snz;

			#pragma omp atomic update
			writing -= 1;        /* unregister as a writing thread */

			if (tid == 0 && (i % verbose_step) == 0) {
				double density =  1.0 * snz / (1.0 * m * Sn);
				fprintf(stderr, "\rSchur complement: %d/%d [%" PRId64 " nz / density= %.3f]", Sn, n, snz, density);
				fflush(stderr);
			}
		}
		free(x);
		free(xj);
	}
	/* finalize S and L */
	if (L)
		L->nz = lnz;
	spasm_csr_realloc(S, -1);
	double density = 1.0 * snz / (1.0 * m * n);
	fprintf(stderr, "\rSchur complement: %d * %d [%" PRId64 " nz / density= %.3f], %.1fs\n", n, m, snz, density, spasm_wtime() - start);
	return S;
}

static void prepare_q(int m, const int *qinv, int *q)
{
	int i = 0;
	for (int j = 0; j < m; j++)
		if (qinv[j] < 0) {
			q[i] = j;
			i += 1;
		}
}

static void gather(int n, const int *xj, const spasm_ZZp *x, void *A, spasm_datatype datatype)
{
	double *Ad;
	float *Af;
	i64 *Ai;
	switch (datatype) {	
	case SPASM_DOUBLE:
		Ad = (double *) A;
		for (int k = 0; k < n; k++) {
			int j = xj[k];
			Ad[k] = x[j];
		}
		break;
	case SPASM_FLOAT:
		Af = (float *) A;
		for (int k = 0; k < n; k++) {
			int j = xj[k];
			Af[k] = x[j];
		}
		break;
	case SPASM_I64:
		Ai = (i64 *) A;
		for (int k = 0; k < n; k++) {
			int j = xj[k];
			Ai[k] = x[j];
		}
		break;
	}
}

static void * row_pointer(void *A, i64 ldA, spasm_datatype datatype, i64 i)
{
	switch (datatype) {	
	case SPASM_DOUBLE: return (double *) A + i*ldA;
	case SPASM_FLOAT: return (float *) A + i*ldA;
	case SPASM_I64: return (i64 *) A + i*ldA;
	}	
	assert(false);
}

/*
 * Computes the dense schur complement of (P*A)[0:n] w.r.t. U. 
 * S must be preallocated of dimension n * (A->m - U->n)
 * zero rows are not written to S.
 * return the number of rows actually written to S.
 * S implicitly has dimension k x (m - npiv), row major, lds == m-npiv.
 * q must be preallocated of size at least (m - U->n).
 * on output, q sends columns of S to non-pivotal columns of A
 * p_out must be of size n, p_int of size A->n
 *
 * TODO: detect empty rows ; push them to the end.
 */
void spasm_schur_dense(const struct spasm_csr *A, const int *p, int n, const int *p_in, 
	struct spasm_lu *fact, void *S, spasm_datatype datatype,int *q, int *p_out)
{
	assert(p != NULL);
	const struct spasm_csr *U = fact->U;
	const int *qinv = fact->qinv;
	int m = A->m;
	int Sm = m - U->n;                                   /* #columns of S */
	prepare_q(m, qinv, q);                               /* FIXME: useless if many invokations */
	fprintf(stderr, "[schur/dense] dimension %d x %d...\n", n, Sm);
	double start = spasm_wtime();
	int verbose_step = spasm_max(1, n / 1000);
	int r = 0;
	struct spasm_triplet *L = fact->Ltmp;
	i64 extra_lnz = 1 + (i64) n * fact->U->n;
	i64 lnz = 0;
	if (L != NULL) {
		lnz = L->nz;
		spasm_triplet_realloc(L, lnz + extra_lnz);
	}
	int *Li = (L != NULL) ? L->i : NULL;
	int *Lj = (L != NULL) ? L->j : NULL;
	spasm_ZZp *Lx = (L != NULL) ? L->x : NULL;

	#pragma omp parallel
	{
		/* per-thread scratch space */
		spasm_ZZp *x = (spasm_ZZp *) spasm_malloc(m * sizeof(*x));
		int *xj = (int *) spasm_malloc(3 * m * sizeof(*xj));
		for (int j = 0; j < 3 * m; j++)
			xj[j] = 0;
		int tid = spasm_get_thread_num();

		#pragma omp for schedule(dynamic, verbose_step)
		for (int k = 0; k < n; k++) {
			int i = p[k];          /* corresponding row of A */
			int iorig = (p_in != NULL) ? p_in[i] : i;
			p_out[k] = iorig;

			/* eliminate known sparse pivots, put result in x */
			for (int j = 0; j < m; j++)
				x[j] = 0;
			int top = spasm_sparse_triangular_solve(U, A, i, xj, x, qinv);

			/* gather x into S[k] */
			void *Sk = row_pointer(S, Sm, datatype, k);
			gather(Sm, q, x, Sk, datatype);
			
			/* fill eliminations coeffs in L */
			if (L != NULL)
				for (int k = top; k < m; k++) {
					int j = xj[k];
					int i = qinv[j];
					if (i < 0 || x[j] == 0)
						continue;
					i64 local_nz;
					#pragma omp atomic capture
					{ local_nz = L->nz; L->nz += 1; } 
					Li[local_nz] = iorig;
					Lj[local_nz] = i;
					Lx[local_nz] = x[j];
				}

			
			/* verbosity */
			#pragma omp atomic update
			r += 1;
			// if (tid == 0 && (r % verbose_step) == 0) {
			// 	fprintf(stderr, "\r[schur/dense] %d/%d", r, n);
			// 	fflush(stderr);
			// }
		}
		free(x);
		free(xj);
	}
	fprintf(stderr, "\n[schur/dense] finished in %.1fs, rank <= %d\n", spasm_wtime() - start, r);
}


/*
 * Computes N random linear combinations rows of the Schur complement of (P*A)[0:n] w.r.t. U.
 * Assumes that pivots are first entries of the row
 * if w > 0, take random linear combinations of subsets of w rows, 
 *    otherwise, take random linear combinations of all the rows
 * S must be preallocated of dimension N * (A->m - U->n)
 * S implicitly has dimension N x (m - npiv), row major, lds == m-npiv.
 * q must be preallocated of size at least (m - U->n).
 * on output, q sends columns of S to non-pivotal columns of A
 */
void spasm_schur_dense_randomized(const struct spasm_csr *A, const int *p, int n, const struct spasm_csr *U, const int *qinv, 
	void *S, spasm_datatype datatype, int *q, int N, int w)
{
	assert(p != NULL);
	assert(n > 0);
	int m = A->m;
	int Sm = m - U->n;
	i64 prime = spasm_get_prime(A);
	const i64 *Up = U->p;
	const int *Uj = U->j;
	prepare_q(m, qinv, q);
	fprintf(stderr, "[schur/dense/random] dimension %d x %d, weight %d...\n", N, Sm, w);
	double start = spasm_wtime();
	int verbose_step = spasm_max(1, N / 1000);

	#pragma omp parallel
	{
		/* per-thread scratch space */
		spasm_ZZp *y = (spasm_ZZp *) spasm_malloc(m * sizeof(*y));

		#pragma omp for schedule(dynamic, verbose_step)
		for (i64 k = 0; k < N; k++) {
			spasm_prng_ctx ctx;
			spasm_prng_seed_simple(prime, k, 0, &ctx);

			for (int j = 0; j < m; j++)
				y[j] = 0;
			if (w <= 0) {
				/* x <--- random linear combinations of all rows */
				for (int i = 0; i < n; i++) {
					int inew = p[i];
					int coeff = spasm_prng_ZZp(&ctx);
					spasm_scatter(A, inew, coeff, y);
				}
			} else {
				for (int i = 0; i < w; i++) {
					int inew = p[rand() % n];
					int coeff = (i == 0) ? 1 : spasm_prng_ZZp(&ctx);
					spasm_scatter(A, inew, coeff, y);
				}
			}

			/* eliminate known sparse pivots */
			for (int i = 0; i < U->n; i++) {
				int j = Uj[Up[i]];               // warning: this assumes pivots are first entries on the row
				if (y[j] == 0)
					continue;
				spasm_scatter(U, i, -y[j], y);
			}
			
			/* gather x into S[k] */
			void *Sk = row_pointer(S, Sm, datatype, k);
			gather(Sm, q, y, Sk, datatype);
			// for (int j = 0; j < Sm; j++) {
			// 	int jj = q[j];
			// 	spasm_datatype_write(S, k * Sm + j, datatype, x[jj]);
			// }

			/* verbosity */
			if ((k % verbose_step) == 0) {
				fprintf(stderr, "\r[schur/dense/random] %" PRId64 "/%d", k, N);
				fflush(stderr);
			}
		}
		free(y);
	}
	fprintf(stderr, "\n[schur/dense/random] finished in %.1fs\n", spasm_wtime() - start);
}

// end of spasm-master/src/spasm_schur.c

// start of spasm_pivots.c
#include <assert.h>
#include <stdlib.h>


/*
 * General convention: in U, the pivot is the first entry of the row.
 */

/* register a pivot in (i, j) ; return 1 iff it is new in both row i or col j */
static int register_pivot(int i, int j, int *pinv, int *qinv)
{
	int r = 1;
	int pinvi = pinv[i];
	int qinvj = qinv[j];
	assert(pinvi < 0 || qinvj < 0);
	if (pinvi != -1) {
		assert(qinv[pinvi] == i);
		assert(pinvi != j);
		qinv[pinvi] = -1;
		r = 0;
	}
	if (qinvj != -1) {
		assert(pinv[qinvj] == j);
		assert(qinvj != i);
		pinv[qinvj] = -1;
		r = 0;
	}
	pinv[i] = j;
	qinv[j] = i;
	return r;
}

/** Faugère-Lachartre pivot search.
 *
 * The leftmost entry of each row is a candidate pivot. Select the sparsest row
 * with a leftmost entry on the given column.
 *
 * update p/qinv and returns the number of pivots found. 
 */
static int spasm_find_FL_pivots(const struct spasm_csr *A, int *p, int *qinv)
{
	int n = A->n;
	int m = A->m;
	const i64 *Ap = A->p;
	const int *Aj = A->j;
	const spasm_ZZp *Ax = A->x;
	double start = spasm_wtime();
	int npiv = 0;

	for (int i = 0; i < n; i++) {
		int j = m + 1;         /* locate leftmost entry */
		for (i64 px = Ap[i]; px < Ap[i + 1]; px++) {
			assert(Ax[px] != 0);
			if (Aj[px] < j)
				j = Aj[px];
		}
		if (j == m + 1)            /* Skip empty rows */
			continue;
		/* check if it is a sparser pivot */
		if (qinv[j] == -1 || spasm_row_weight(A, i) < spasm_row_weight(A, qinv[j]))
			npiv += register_pivot(i, j, p, qinv);
	}
	fprintf(stderr, "[pivots] Faugère-Lachartre: %d pivots found [%.1fs]\n", npiv, spasm_wtime() - start);
	return npiv;
}


/*
 * Leftovers from FL. Column not occuring on previously selected pivot row
 * can be made pivotal, as this will not create alternating cycles.
 * 
 * w[j] = 1 <===> column j does not appear in a pivotal row
 * 
 */
static int spasm_find_FL_column_pivots(const struct spasm_csr *A, int *pinv, int *qinv)
{
	int n = A->n;
	int m = A->m;
	const i64 *Ap = A->p;
	const int *Aj = A->j;
	int npiv = 0;
	int *w = (int *) spasm_malloc(m * sizeof(int));
	for (int j = 0; j < m; j++)
		w[j] = 1;
	double start = spasm_wtime();

	/* mark columns on pivotal rows as obstructed */
	for (int i = 0; i < n; i++) {
		if (pinv[i] < 0)
			continue;
		for (i64 px = Ap[i]; px < Ap[i + 1]; px++) {
			int j = Aj[px];
			w[j] = 0;
		}
	}

	/* find new pivots */
	for (int i = 0; i < n; i++) {
		if (pinv[i] >= 0)
			continue;

		/* does A[i,:] have an entry on an unobstructed column? */
		for (i64 px = Ap[i]; px < Ap[i + 1]; px++) {
			int j = Aj[px];
			if (w[j] == 0)
				continue;	/* this column is closed, skip this entry */
			if (qinv[j] >= 0)
				continue;       /* column j already pivotal */
			/* TODO: displace previous pivot on column j if this one is better */
			npiv += register_pivot(i, j, pinv, qinv);
			/* mark the columns occuring on this row as unavailable */
			for (i64 px = Ap[i]; px < Ap[i + 1]; px++) 
				w[Aj[px]] = 0;
			break; /* move on to the next row */
		}
	}
	free(w);
	fprintf(stderr, "[pivots] ``Faugère-Lachartre on columns'': %d pivots found [%.1fs]\n", 
		npiv, spasm_wtime() - start);
	return npiv;
}


/*
 * This implements the greedy parallel algorithm described in
 * https://doi.org/10.1145/3115936.3115944
 */
static inline void BFS_enqueue(char *w, int *queue, int *surviving, int *tail, int j)
{
	queue[(*tail)++] = j;
	*surviving -= w[j];
	w[j] = -1;
}

static inline void BFS_enqueue_row(char *w, int *queue, int *surviving, int *tail, const i64 *Ap, const int *Aj, int i) 
{
	for (i64 px = Ap[i]; px < Ap[i + 1]; px++) {
		/* this is the critical section */
		int j = Aj[px];
		if (w[j] >= 0)
			BFS_enqueue(w, queue, surviving, tail, j);
	}
}

static int spasm_find_cycle_free_pivots(const struct spasm_csr *A, int *pinv, int *qinv)
{
	int n = A->n;
	int m = A->m;
	const i64 *Ap = A->p;
	const int *Aj = A->j;
	int v = spasm_max(1, spasm_min(1000, n / 100));
	int processed = 0;
	int npiv = 0;
	double start = spasm_wtime();
	int *journal = (int *) spasm_malloc(n * sizeof(*journal));

	/*
	 * This uses "transactions". Rows with new pivots are appended to the journal.
	 * npiv is the number of such rows. If npiv has not changed since the beginning of
	 * a transaction, then it can be commited right away.
	 */
	#pragma omp parallel
	{
		char *w = (char *) spasm_malloc(m * sizeof(*w));
		int *queue = (int *) spasm_malloc(m * sizeof(*queue));

		/* workspace initialization */
		int tid = spasm_get_thread_num();
		for(int j = 0; j < m; j++)
			w[j] = 0;

		#pragma omp for schedule(dynamic, 1000)
		for (int i = 0; i < n; i++) {
			/*
			 * for each non-pivotal row, computes the columns reachable from its entries by alternating paths.
			 * Unreachable entries on the row can be chosen as pivots. 
			 * The w[] array is used for marking during the graph traversal. 
			 * Before the search: 
			 *   w[j] == 1 for each non-pivotal entry j on the row 
			 *   w[j] == 0 otherwise 
			 * After the search: 
			 *   w[j] ==  1  for each unreachable non-pivotal entry j on the row (candidate pivot) 
			 *   w[j] == -1  column j is reachable by an alternating path,
			 *                 or is pivotal (has entered the queue at some point) 
			 *   w[j] ==  0  column j was absent and is unreachable
			 */
			if ((tid == 0) && (i % v) == 0) {
				fprintf(stderr, "\r[pivots] %d / %d --- found %d new", processed, n, npiv);
				fflush(stderr);
			}
			if (pinv[i] >= 0)
				continue;   /* row is already pivotal */

			#pragma omp atomic update
			processed++;

			/* we will start reading qinv: begin the transaction by reading npiv */
			int npiv_local;
			#pragma omp atomic read
			npiv_local = npiv;

			/* scatters columns of A[i] into w, enqueue pivotal entries */
			int head = 0;
			int tail = 0;
			int surviving = 0;
			for (i64 px = Ap[i]; px < Ap[i + 1]; px++) {
				int j = Aj[px];
				if (qinv[j] < 0) {
					w[j] = 1;
					surviving += 1;
				} else {
					BFS_enqueue(w, queue, &surviving, &tail, j);
				}
			}

			/* BFS. This is where most of the time is spent */
	int npiv_target, j;

	BFS:		while (head < tail && surviving > 0) {
				int j = queue[head++];
				int I = qinv[j];
				if (I == -1)
					continue;	/* j is not pivotal: nothing to do */
				BFS_enqueue_row(w, queue, &surviving, &tail, Ap, Aj, I);
			}

			/* scan w for surviving entries */
			if (surviving == 0)
				goto cleanup;   /* no possible pivot */
			
			/* locate survivor in the row */
			j = -1;
			for (i64 px = Ap[i]; px < Ap[i + 1]; px++) {
				j = Aj[px];
				if (w[j] == 1)  /* potential pivot */
					break;
			}
			assert(j != -1);

			/* try to commit the transaction */
			npiv_target = -1;
			#pragma omp critical
			{
				if (npiv == npiv_local) {
					/* success */
					int result = register_pivot(i, j, pinv, qinv);
					journal[npiv] = j;
					#pragma omp atomic update
					npiv += result;
				} else {
					/* failure */
					#pragma omp atomic read
					npiv_target = npiv;
				}
			}

			if (npiv_target < 0)
				goto cleanup;  /* commit success */

			/* commit failure: new pivots have been found behind our back. Examine them */
			for (; npiv_local < npiv_target; npiv_local++) {
				int j = journal[npiv_local];
				if (w[j] == 0)	/* the new pivot plays no role here */
					continue;
				if (w[j] == 1) {
					/* a survivor becomes pivotal with this pivot */
					BFS_enqueue(w, queue, &surviving, &tail, j);
				} else {
					/* the new pivot has been hit */
					int i = qinv[j];
					BFS_enqueue_row(w, queue, &surviving, &tail, Ap, Aj, i);
				}
			}
			goto BFS;

	
			/* reset w back to zero */
	cleanup:		for (i64 px = Ap[i]; px < Ap[i + 1]; px++) {
				int j = Aj[px];
				w[j] = 0;
			}
			for (int px = 0; px < tail; px++) {
				int j = queue[px];
				w[j] = 0;
			}
		}
		free(w);
		free(queue);
	}
	free(journal);
	fprintf(stderr, "\r[pivots] greedy alternating cycle-free search: %d pivots found [%.1fs]\n", 
		npiv, spasm_wtime() - start);
	return npiv;
}

/*
 * Find a permutation of rows/columns that selects pivots without arithmetic operations.
 * Return the number of pivots found. 
 * qinv[j] == i if (i, j) is a pivot or -1 if there is no pivot on column j.
 * pinv[i] == j if (i, j) is a pivot or -1 if there is no pivot on row i.
 *
 * p : row permutations. Pivotal rows are first, in topological order 
 * Both p, pinv and qinv must be preallocated
 */
static int spasm_pivots_find(const struct spasm_csr *A, int *pinv, int *qinv, struct echelonize_opts *opts)
{
	int n = A->n;
	int m = A->m;
	for (int j = 0; j < m; j++)
		qinv[j] = -1;
	for (int i = 0; i < n; i++)
		pinv[i] = -1;
	int npiv = spasm_find_FL_pivots(A, pinv, qinv);
	npiv += spasm_find_FL_column_pivots(A, pinv, qinv);	
	if (opts->enable_greedy_pivot_search)
		npiv += spasm_find_cycle_free_pivots(A, pinv, qinv);
	fprintf(stderr, "\r[pivots] %d pivots found\n", npiv);
	return npiv;
}

/*
 * build row permutation p. Pivotal rows go first in topological order,
 * then non-pivotal rows
 */
static void spasm_pivots_reorder(const struct spasm_csr *A, const int *pinv, 
	                             const int *qinv, int npiv, int *p)
{
	int n = A->n;
	int m = A->m;
	int k = 0;

	/* topological sort */
	int *xj = (int *) spasm_malloc(m * sizeof(*xj));
	int *marks = (int *) spasm_malloc(m * sizeof(*marks));
	int *pstack = (int *) spasm_malloc(m * sizeof(*pstack));
	for (int j = 0; j < m; j++)
		marks[j] = 0;
	int top = m;
	for (int j = 0; j < m; j++)
		if (qinv[j] != -1 && !marks[j])
			top = spasm_dfs(j, A, top, xj, pstack, marks, qinv);
	/* now produce the permutation p that puts pivotal rows first, in order */
	for (int px = top; px < m; px++) {
		int j = xj[px];
		int i = qinv[j];
		if (i != -1) {
			assert(pinv[i] == j);
			p[k] = i;
			k += 1;
		}
	}
	assert(k == npiv);
	for (int i = 0; i < n; i++)
		if (pinv[i] == -1) {
			p[k] = i;
			k += 1;
		}
	assert(k == n);
	free(xj);
	free(marks);
	free(pstack);
}

/*
 * Identify stuctural pivots in A, and copy the relevant rows to U / update L if present
 * write p (pivotal rows of A first)
 * return the number of pivots found
 */
int spasm_pivots_extract_structural(const struct spasm_csr *A, const int *p_in, struct spasm_lu *fact, 
								    int *p, struct echelonize_opts *opts)
{
	int n = A->n;
	int m = A->m;
	int *qinv = (int *) spasm_malloc(m * sizeof(*qinv));     /* for pivot search */
	int *pinv = (int *) spasm_malloc(n * sizeof(*pinv));     /* for pivot search */

	/* find structural pivots in A */
	int npiv = spasm_pivots_find(A, pinv, qinv, opts);

	/* reorder pivots to make U upper-triangular (up to a column permutation) */
	spasm_pivots_reorder(A, pinv, qinv, npiv, p);

	/* compute total pivot nnz and reallocate U if necessary */
	struct spasm_csr *U = fact->U;
	struct spasm_triplet *L = fact->Ltmp;
	int *Uqinv = fact->qinv;
	int *Lp = fact->p;
	i64 pivot_nnz = 0;
	for (int k = 0; k < npiv; k++) {
		int i = p[k];
		pivot_nnz += spasm_row_weight(A, i);
	}
	if (spasm_nnz(U) + pivot_nnz > U->nzmax)
		spasm_csr_realloc(U, spasm_nnz(U) + pivot_nnz);

	/* copy pivotal rows to U and make them unitary; update Uqinv */
	const i64 *Ap = A->p;
	const int *Aj = A->j;
	const spasm_ZZp *Ax = A->x;
	i64 *Up = U->p;
	int *Uj = U->j;
	spasm_ZZp *Ux = U->x;
	i64 unz = spasm_nnz(U);

	for (int k = 0; k < npiv; k++) {
		int i = p[k];
		int j = pinv[i];
		assert(j >= 0);
		assert(qinv[j] == i);
		
		Uqinv[j] = U->n;          /* register pivot in U */
		/* locate pivot in row */ 
		spasm_ZZp pivot = 0;
		for (i64 px = Ap[i]; px < Ap[i + 1]; px++) {
			if ((Aj[px] == j) && (Ax[px] != 0)) {
				pivot = Ax[px];
				break;
			}
		}
		assert(pivot != 0);
		if (L != NULL) {
			int i_out = (p_in != NULL) ? p_in[i] : i;
			spasm_add_entry(L, i_out, U->n, pivot);
			// fprintf(stderr, "Adding L[%d, %d] = %d\n", i_out, U->n, pivot);
			Lp[U->n] = i_out;
		}

		/* make pivot unitary and add it first */
		spasm_ZZp alpha = spasm_ZZp_inverse(A->field, pivot);
		Uj[unz] = j;
		Ux[unz] = 1;
		unz += 1;
		/* add the rest of the row */
		for (i64 px = Ap[i]; px < Ap[i + 1]; px++) {
			if (j == Aj[px])
				continue;    /* skip pivot, already there */
			Uj[unz] = Aj[px];
			Ux[unz] = spasm_ZZp_mul(A->field, alpha, Ax[px]);
			unz += 1;
		}
		U->n += 1;
		Up[U->n] = unz;
	}
	assert(unz <= U->nzmax);
	free(pinv);
	free(qinv);
	return npiv;
}

#if 0
/*
 * returns a permuted version of A where pivots are pushed to the top-left
 * and form an upper-triangular principal submatrix. qinv is modified.
 */
struct spasm_csr *spasm_permute_pivots(const struct spasm_csr *A, const int *p, int *qinv, int npiv)
{
	int m = A->m;
	const i64 *Ap = A->p;
	const int *Aj = A->j;

	/* pivotal columns first */
	int k = 0;
	for (int i = 0; i < npiv; i++) {
		/* the pivot is the first entry of each row */
		int inew = p[i];
		int j = Aj[Ap[inew]];
		qinv[j] = k;
		k += 1;
	}

	/* put remaining non-pivotal columns afterwards, in any order */
	for (int j = 0; j < m; j++)
		if (qinv[j] == -1) {
			qinv[j] = k;
			k += 1;
		}
	return spasm_permute(A, p, qinv, true);
}
#endif

// end of spasm-master/src/spasm_pivots.c

// start of sha256.c
/*
 * Copyright 2004-2016 The OpenSSL Project Authors. All Rights Reserved.
 *
 * Licensed under the OpenSSL license (the "License").  You may not use
 * this file except in compliance with the License.  You can obtain a copy
 * in the file LICENSE in the source distribution or at
 * https://www.openssl.org/source/license.html
 *
 * modified by C. Bouillaguet
 */
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#define SHA_LONG        u32
#define SHA256_DIGEST_LENGTH    32
#define SHA256_CBLOCK   (SHA_LBLOCK*4)/* SHA-256 treats input data as a
                                        * contiguous array of 32 bit wide
                                        * big-endian values. */

#define SHA_LBLOCK      16
#define SHA_CBLOCK      (SHA_LBLOCK*4)/* SHA treats input data as a
                                        * contiguous array of 32 bit wide
                                        * big-endian values. */
#define SHA_LAST_BLOCK  (SHA_CBLOCK-8)
#define SHA_DIGEST_LENGTH 20
#define SHA224_DIGEST_LENGTH    28
#define MD32_REG_T int

// typedef void *(*memset_t)(void *, int, size_t);
// static volatile memset_t memset_func = memset;

static void OPENSSL_cleanse(void *ptr, size_t len)
{
    memset(ptr, 0, len);
}

void spasm_SHA256_init(spasm_sha256_ctx *c)
{
    memset(c, 0, sizeof(*c));
    c->h[0] = 0x6a09e667UL;
    c->h[1] = 0xbb67ae85UL;
    c->h[2] = 0x3c6ef372UL;
    c->h[3] = 0xa54ff53aUL;
    c->h[4] = 0x510e527fUL;
    c->h[5] = 0x9b05688cUL;
    c->h[6] = 0x1f83d9abUL;
    c->h[7] = 0x5be0cd19UL;
    c->md_len = SHA256_DIGEST_LENGTH;
}

#define DATA_ORDER_IS_BIG_ENDIAN
#define HASH_LONG               SHA_LONG
#define HASH_CTX                spasm_sha256_ctx
#define HASH_CBLOCK             SHA_CBLOCK

/*
 * Note that FIPS180-2 discusses "Truncation of the Hash Function Output."
 * default: case below covers for it. It's not clear however if it's
 * permitted to truncate to amount of bytes not divisible by 4. I bet not,
 * but if it is, then default: case shall be extended. For reference.
 * Idea behind separate cases for pre-defined lengths is to let the
 * compiler decide if it's appropriate to unroll small loops.
 */
#define HASH_MAKE_STRING(c,s)   do {    \
        u64 ll;               \
        u32  nn;              \
        assert((c)->md_len == SHA256_DIGEST_LENGTH);         \
        for (nn=0;nn<SHA256_DIGEST_LENGTH/4;nn++)               \
            {   ll=(c)->h[nn]; (void)HOST_l2c(ll,(s));   }      \
        } while (0)

// #define HASH_TRANSFORM          SHA256_Transform
// #define HASH_FINAL              SHA256_Final
// #define HASH_BLOCK_DATA_ORDER   sha256_block_data_order

static void sha256_block_data_order(spasm_sha256_ctx *ctx, const void *in, size_t num);

#define ROTATE(a,n)     (((a)<<(n))|(((a)&0xffffffff)>>(32-(n))))
#define HOST_c2l(c,l)   (l =(((u64)(*((c)++)))<<24),          \
                         l|=(((u64)(*((c)++)))<<16),          \
                         l|=(((u64)(*((c)++)))<< 8),          \
                         l|=(((u64)(*((c)++)))    )           )
#define HOST_l2c(l,c)   (*((c)++)=(u8)(((l)>>24)&0xff),      \
                         *((c)++)=(u8)(((l)>>16)&0xff),      \
                         *((c)++)=(u8)(((l)>> 8)&0xff),      \
                         *((c)++)=(u8)(((l)    )&0xff),      \
                         l)



void spasm_SHA256_update(spasm_sha256_ctx *c, const void *data_, size_t len)
{
    const u8 *data = (const u8 *) data_;
    u8 *p;
    SHA_LONG l;
    size_t n;

    if (len == 0)
        return;

    l = (c->Nl + (((HASH_LONG) len) << 3)) & 0xffffffffUL;
    if (l < c->Nl)              /* overflow */
        c->Nh++;
    c->Nh += (HASH_LONG) (len >> 29); /* might cause compiler warning on
                                       * 16-bit */
    c->Nl = l;

    n = c->num;
    if (n != 0) {
        p = (u8 *)c->data;

        if (len >= HASH_CBLOCK || len + n >= HASH_CBLOCK) {
            memcpy(p + n, data, HASH_CBLOCK - n);
            sha256_block_data_order(c, p, 1);
            n = HASH_CBLOCK - n;
            data += n;
            len -= n;
            c->num = 0;
            /*
             * We use memset rather than OPENSSL_cleanse() here deliberately.
             * Using OPENSSL_cleanse() here could be a performance issue. It
             * will get properly cleansed on finalisation so this isn't a
             * security problem.
             */
            memset(p, 0, HASH_CBLOCK); /* keep it zeroed */
        } else {
            memcpy(p + n, data, len);
            c->num += (u32)len;
            return;
        }
    }

    n = len / HASH_CBLOCK;
    if (n > 0) {
        sha256_block_data_order(c, data, n);
        n *= HASH_CBLOCK;
        data += n;
        len -= n;
    }

    if (len != 0) {
        p = (u8 *)c->data;
        c->num = (u32)len;
        memcpy(p, data, len);
    }
    return;
}

void spasm_SHA256_final(u8 *md, HASH_CTX *c)
{
    u8 *p = (u8 *)c->data;
    size_t n = c->num;

    p[n] = 0x80;                /* there is always room for one */
    n++;

    if (n > (HASH_CBLOCK - 8)) {
        memset(p + n, 0, HASH_CBLOCK - n);
        n = 0;
        sha256_block_data_order(c, p, 1);
    }
    memset(p + n, 0, HASH_CBLOCK - 8 - n);

    p += HASH_CBLOCK - 8;
    (void)HOST_l2c(c->Nh, p);
    (void)HOST_l2c(c->Nl, p);
    p -= HASH_CBLOCK;
    sha256_block_data_order(c, p, 1);
    c->num = 0;
    OPENSSL_cleanse(p, HASH_CBLOCK);

    HASH_MAKE_STRING(c, md);
}


static const SHA_LONG K256[64] = {
    0x428a2f98UL, 0x71374491UL, 0xb5c0fbcfUL, 0xe9b5dba5UL,
    0x3956c25bUL, 0x59f111f1UL, 0x923f82a4UL, 0xab1c5ed5UL,
    0xd807aa98UL, 0x12835b01UL, 0x243185beUL, 0x550c7dc3UL,
    0x72be5d74UL, 0x80deb1feUL, 0x9bdc06a7UL, 0xc19bf174UL,
    0xe49b69c1UL, 0xefbe4786UL, 0x0fc19dc6UL, 0x240ca1ccUL,
    0x2de92c6fUL, 0x4a7484aaUL, 0x5cb0a9dcUL, 0x76f988daUL,
    0x983e5152UL, 0xa831c66dUL, 0xb00327c8UL, 0xbf597fc7UL,
    0xc6e00bf3UL, 0xd5a79147UL, 0x06ca6351UL, 0x14292967UL,
    0x27b70a85UL, 0x2e1b2138UL, 0x4d2c6dfcUL, 0x53380d13UL,
    0x650a7354UL, 0x766a0abbUL, 0x81c2c92eUL, 0x92722c85UL,
    0xa2bfe8a1UL, 0xa81a664bUL, 0xc24b8b70UL, 0xc76c51a3UL,
    0xd192e819UL, 0xd6990624UL, 0xf40e3585UL, 0x106aa070UL,
    0x19a4c116UL, 0x1e376c08UL, 0x2748774cUL, 0x34b0bcb5UL,
    0x391c0cb3UL, 0x4ed8aa4aUL, 0x5b9cca4fUL, 0x682e6ff3UL,
    0x748f82eeUL, 0x78a5636fUL, 0x84c87814UL, 0x8cc70208UL,
    0x90befffaUL, 0xa4506cebUL, 0xbef9a3f7UL, 0xc67178f2UL
};

/*
 * FIPS specification refers to right rotations, while our ROTATE macro
 * is left one. This is why you might notice that rotation coefficients
 * differ from those observed in FIPS document by 32-N...
 */
# define Sigma0(x)       (ROTATE((x),30) ^ ROTATE((x),19) ^ ROTATE((x),10))
# define Sigma1(x)       (ROTATE((x),26) ^ ROTATE((x),21) ^ ROTATE((x),7))
# define sigma0(x)       (ROTATE((x),25) ^ ROTATE((x),14) ^ ((x)>>3))
# define sigma1(x)       (ROTATE((x),15) ^ ROTATE((x),13) ^ ((x)>>10))

# define Ch(x,y,z)       (((x) & (y)) ^ ((~(x)) & (z)))
# define Maj(x,y,z)      (((x) & (y)) ^ ((x) & (z)) ^ ((y) & (z)))

#  define ROUND_00_15(i,a,b,c,d,e,f,g,h)          do {    \
        T1 += h + Sigma1(e) + Ch(e,f,g) + K256[i];      \
        h = Sigma0(a) + Maj(a,b,c);                     \
        d += T1;        h += T1;                } while (0)

#  define ROUND_16_63(i,a,b,c,d,e,f,g,h,X)        do {    \
        s0 = X[(i+1)&0x0f];     s0 = sigma0(s0);        \
        s1 = X[(i+14)&0x0f];    s1 = sigma1(s1);        \
        T1 = X[(i)&0x0f] += s0 + s1 + X[(i+9)&0x0f];    \
        ROUND_00_15(i,a,b,c,d,e,f,g,h);         } while (0)

static void sha256_block_data_order(spasm_sha256_ctx *ctx, const void *in, size_t num)
{
    unsigned MD32_REG_T a, b, c, d, e, f, g, h, s0, s1, T1;
    SHA_LONG X[16];
    int i;
    const u8 *data = (const u8 *) in;
    const union {
        long one;
        char little;
    } is_endian = {
        1
    };

    while (num--) {

        a = ctx->h[0];
        b = ctx->h[1];
        c = ctx->h[2];
        d = ctx->h[3];
        e = ctx->h[4];
        f = ctx->h[5];
        g = ctx->h[6];
        h = ctx->h[7];

        if (!is_endian.little && sizeof(SHA_LONG) == 4
            && ((size_t)in % 4) == 0) {
            const SHA_LONG *W = (const SHA_LONG *)data;

            T1 = X[0] = W[0];
            ROUND_00_15(0, a, b, c, d, e, f, g, h);
            T1 = X[1] = W[1];
            ROUND_00_15(1, h, a, b, c, d, e, f, g);
            T1 = X[2] = W[2];
            ROUND_00_15(2, g, h, a, b, c, d, e, f);
            T1 = X[3] = W[3];
            ROUND_00_15(3, f, g, h, a, b, c, d, e);
            T1 = X[4] = W[4];
            ROUND_00_15(4, e, f, g, h, a, b, c, d);
            T1 = X[5] = W[5];
            ROUND_00_15(5, d, e, f, g, h, a, b, c);
            T1 = X[6] = W[6];
            ROUND_00_15(6, c, d, e, f, g, h, a, b);
            T1 = X[7] = W[7];
            ROUND_00_15(7, b, c, d, e, f, g, h, a);
            T1 = X[8] = W[8];
            ROUND_00_15(8, a, b, c, d, e, f, g, h);
            T1 = X[9] = W[9];
            ROUND_00_15(9, h, a, b, c, d, e, f, g);
            T1 = X[10] = W[10];
            ROUND_00_15(10, g, h, a, b, c, d, e, f);
            T1 = X[11] = W[11];
            ROUND_00_15(11, f, g, h, a, b, c, d, e);
            T1 = X[12] = W[12];
            ROUND_00_15(12, e, f, g, h, a, b, c, d);
            T1 = X[13] = W[13];
            ROUND_00_15(13, d, e, f, g, h, a, b, c);
            T1 = X[14] = W[14];
            ROUND_00_15(14, c, d, e, f, g, h, a, b);
            T1 = X[15] = W[15];
            ROUND_00_15(15, b, c, d, e, f, g, h, a);

            data += SHA256_CBLOCK;
        } else {
            SHA_LONG l;

            (void)HOST_c2l(data, l);
            T1 = X[0] = l;
            ROUND_00_15(0, a, b, c, d, e, f, g, h);
            (void)HOST_c2l(data, l);
            T1 = X[1] = l;
            ROUND_00_15(1, h, a, b, c, d, e, f, g);
            (void)HOST_c2l(data, l);
            T1 = X[2] = l;
            ROUND_00_15(2, g, h, a, b, c, d, e, f);
            (void)HOST_c2l(data, l);
            T1 = X[3] = l;
            ROUND_00_15(3, f, g, h, a, b, c, d, e);
            (void)HOST_c2l(data, l);
            T1 = X[4] = l;
            ROUND_00_15(4, e, f, g, h, a, b, c, d);
            (void)HOST_c2l(data, l);
            T1 = X[5] = l;
            ROUND_00_15(5, d, e, f, g, h, a, b, c);
            (void)HOST_c2l(data, l);
            T1 = X[6] = l;
            ROUND_00_15(6, c, d, e, f, g, h, a, b);
            (void)HOST_c2l(data, l);
            T1 = X[7] = l;
            ROUND_00_15(7, b, c, d, e, f, g, h, a);
            (void)HOST_c2l(data, l);
            T1 = X[8] = l;
            ROUND_00_15(8, a, b, c, d, e, f, g, h);
            (void)HOST_c2l(data, l);
            T1 = X[9] = l;
            ROUND_00_15(9, h, a, b, c, d, e, f, g);
            (void)HOST_c2l(data, l);
            T1 = X[10] = l;
            ROUND_00_15(10, g, h, a, b, c, d, e, f);
            (void)HOST_c2l(data, l);
            T1 = X[11] = l;
            ROUND_00_15(11, f, g, h, a, b, c, d, e);
            (void)HOST_c2l(data, l);
            T1 = X[12] = l;
            ROUND_00_15(12, e, f, g, h, a, b, c, d);
            (void)HOST_c2l(data, l);
            T1 = X[13] = l;
            ROUND_00_15(13, d, e, f, g, h, a, b, c);
            (void)HOST_c2l(data, l);
            T1 = X[14] = l;
            ROUND_00_15(14, c, d, e, f, g, h, a, b);
            (void)HOST_c2l(data, l);
            T1 = X[15] = l;
            ROUND_00_15(15, b, c, d, e, f, g, h, a);
        }

        for (i = 16; i < 64; i += 8) {
            ROUND_16_63(i + 0, a, b, c, d, e, f, g, h, X);
            ROUND_16_63(i + 1, h, a, b, c, d, e, f, g, X);
            ROUND_16_63(i + 2, g, h, a, b, c, d, e, f, X);
            ROUND_16_63(i + 3, f, g, h, a, b, c, d, e, X);
            ROUND_16_63(i + 4, e, f, g, h, a, b, c, d, X);
            ROUND_16_63(i + 5, d, e, f, g, h, a, b, c, X);
            ROUND_16_63(i + 6, c, d, e, f, g, h, a, b, X);
            ROUND_16_63(i + 7, b, c, d, e, f, g, h, a, X);
        }

        ctx->h[0] += a;
        ctx->h[1] += b;
        ctx->h[2] += c;
        ctx->h[3] += d;
        ctx->h[4] += e;
        ctx->h[5] += f;
        ctx->h[6] += g;
        ctx->h[7] += h;

    }
}

// end of sha256.c

// start of spasm_triangular.c

#include <stdlib.h>
#include <assert.h>

/*
 * Solving triangular systems, dense RHS
 */


/*
 * Solve x.L = b with dense b and x.
 * x must have size n (#rows of L) and b must have size m (#cols of L)
 * b is destroyed
 * 
 * L is assumed to be (permuted) lower-triangular, with non-zero diagonal.
 * 
 * p[j] == i indicates if the "diagonal" entry on column j is on row i
 * 
 */
void spasm_dense_back_solve(const struct spasm_csr *L, spasm_ZZp *b, spasm_ZZp *x, const int *p)
{
	int n = L->n;
	int r = L->m;
	const i64 *Lp = L->p;
	const int *Lj = L->j;
	const spasm_ZZp *Lx = L->x;
	
	for (int i = 0; i < n; i++)
		x[i] = 0;

	for (int j = r - 1; j >= 0; j--) {
		int i = (p != NULL) ? p[j] : j;
		assert(0 <= i);
		assert(i < n);

		/* scan L[i] to locate the "diagonal" entry on column j */
		spasm_ZZp diagonal_entry = 0;
		for (i64 px = Lp[i]; px < Lp[i + 1]; px++)
			if (Lj[px] == j) {
				diagonal_entry = Lx[px];
				break; 
			}
		assert(diagonal_entry != 0);

		/* axpy - inplace */
		spasm_ZZp alpha = spasm_ZZp_inverse(L->field, diagonal_entry);
		x[i] = spasm_ZZp_mul(L->field, alpha, b[j]);
		spasm_ZZp backup = x[i];
		spasm_scatter(L, i, -x[i], b);
		x[i] = backup;
	}
}

/*
 * Solve x.U = b with dense x, b.
 * 
 * b is destroyed on output
 * 
 * U is (petmuted) upper-triangular with unit diagonal.
 * q[i] == j    means that the pivot on row i is on column j (this is the inverse of the usual qinv). 
 *
 * returns True if a solution was found;
 */
bool spasm_dense_forward_solve(const struct spasm_csr *U, spasm_ZZp *b, spasm_ZZp *x, const int *q)
{
	int n = U->n;
	int m = U->m;
	assert(n <= m);

	for (int i = 0; i < n; i++)
		x[i] = 0;

	for (int i = 0; i < n; i++) {
		int j = (q != NULL) ? q[i] : i;
		
		if (b[j] == 0)
			continue;

		/* eliminate b[j] */
		x[i] = b[j];
		spasm_scatter(U, i, -b[j], b);
		assert(b[j] == 0);
	}
	for (int j = 0; j < m; j++)   /* check that everything has been eliminated */
		if (b[j] != 0)
			return 0;
	return 1;
}

/*
 * solve x * U = B[k], where U is (permuted) triangular (either upper or lower).
 *
 * x must have size m (#columns of U); it does not need to be initialized.
 * xj must be preallocated of size 3*m and zero-initialized (it remains OK)
 * qinv locates the pivots in U.
 *
 * On output, the solution is scattered in x, and its pattern is given in xj[top:m].
 * The precise semantics is as follows. Define:
 *         x_a = { j in [0:m] : qinv[j] < 0 }
 *         x_b = { j in [0:m] : qinv[j] >= 0 }
 * Then x_b * U + x_a == B[k].  It follows that x * U == y has a solution iff x_a is empty.
 * 
 * top is the return value
 *
 * This does not require the pivots to be the first entry of the row.
 * This requires that the pivots in U are all equal to 1. 
 */
int spasm_sparse_triangular_solve(const struct spasm_csr *U, const struct spasm_csr *B, int k, int *xj, spasm_ZZp * x, const int *qinv)
{
	int m = U->m;
	assert(qinv != NULL);
	// const i64 *Bp = B->p;
	// const int *Bj = B->j;
	// const spasm_ZZp *Bx = B->x;

	/* compute non-zero pattern of x --- xj[top:m] = Reach(U, B[k]) */
	int top = spasm_reach(U, B, k, m, xj, qinv);

	/* clear x and scatter B[k] into x*/
	for (int px = top; px < m; px++) {
		int j = xj[px];
		x[j] = 0;
	}
	spasm_scatter(B, k, 1, x);
	// for (i64 px = Bp[k]; px < Bp[k + 1]; px++) {
	// 	int j = Bj[px];
	// 	x[j] = Bx[px];
	// }

	/* iterate over the (precomputed) pattern of x (= the solution) */
	for (int px = top; px < m; px++) {
		int j = xj[px];          /* x[j] is generically nonzero, (i.e., barring numerical cancelation) */

		/* locate corresponding pivot if there is any */
		int i = qinv[j];
		if (i < 0)
			continue;

		/* the pivot entry on row i is 1, so we just have to multiply by -x[j] */
		spasm_ZZp backup = x[j];
		spasm_scatter(U, i, -x[j], x);
		assert(x[j] == 0);
		x[j] = backup;
	}
	return top;
}

// end of spasm-master/src/spasm_triangular.c

// start of spasm_prng.c
#include <arpa/inet.h>           // htonl

/* This PRNG is SHA256 in counter mode */

static void rehash(spasm_prng_ctx *ctx)
{
        spasm_sha256_ctx hctx;
        spasm_SHA256_init(&hctx);
        spasm_SHA256_update(&hctx, ctx->block, 44);
        spasm_SHA256_final((u8 *) ctx->hash, &hctx);
        ctx->counter += 1;
        ctx->block[9] = htonl(ctx->counter);
        ctx->i = 0;
}

/*
 * Return a uniformly random 32-bit integer
 */
u32 spasm_prng_u32(spasm_prng_ctx *ctx)
{
        if (ctx->i == 8)
                rehash(ctx);
        u32 res = ctx->hash[ctx->i];
        ctx->i += 1;
        return htonl(res);
}

/*
 * Return a uniformly integer modulo prime (rejection sampling)
 */
spasm_ZZp spasm_prng_ZZp(spasm_prng_ctx *ctx)
{
        for (;;) {
                u32 x = spasm_prng_u32(ctx) & ctx->mask;
                if (x < ctx->prime)
                        return spasm_ZZp_init(ctx->field, x);
        }
}

/*
 * Seed must be 32 bytes.
 */
void spasm_prng_seed(const u8 *seed, i64 prime, u32 seq, spasm_prng_ctx *ctx)
{
        u8 *block8 = (u8 *) ctx->block;
        for (int i = 0; i < 32; i++)
                block8[i] = seed[i];
        ctx->prime = prime;
        i64 mask = 1;
        while (mask < prime)
                mask <<= 1;
        ctx->mask = mask - 1;
        ctx->block[8] = htonl(prime);
        ctx->block[9] = 0;
        ctx->block[10] = htonl(seq);
        ctx->counter = 0;
        spasm_field_init(prime, ctx->field);
        rehash(ctx);
}

/*
 * In case where a 32-byte seed (i.e. a SHA256 digest) is not available
 */
void spasm_prng_seed_simple(i64 prime, u64 seed, u32 seq, spasm_prng_ctx *ctx)
{
        u32 block[8];
        block[0] = htonl(seed & 0xffffffff);
        block[1] = htonl(seed >> 32);
        for (int i = 2; i < 8; i++)
                block[i] = 0;
        spasm_prng_seed((u8 *) block, prime, seq, ctx);
}

// end of spasm-master/src/spasm_prng.c

// start of spasm_solve.c
#include <assert.h>
#include <stdlib.h>

/*
 * Solve x.A = b
 * 
 * b has size m (#columns of A), solution has size n.
 * 
 * returns true if a solution exists
 */
bool spasm_solve(const struct spasm_lu *fact, const spasm_ZZp *b, spasm_ZZp *x)
{
	const struct spasm_csr *L = fact->L;
	const struct spasm_csr *U = fact->U;
	assert(L != NULL);
	// int n = L->n;
	int m = U->m;
	int r = U->n;   /* rank */

	/* get workspace */
	spasm_ZZp *y = (spasm_ZZp *) spasm_malloc(m * sizeof(*y));
	spasm_ZZp *z = (spasm_ZZp *) spasm_malloc(r * sizeof(*z));
	
	/* inverse permutation for U */
	int *Uq = (int *) spasm_malloc(r * sizeof(*Uq));
	const int *qinv = fact->qinv;
	for (int j = 0; j < m; j++) {
		int i = qinv[j];
		if (i != -1)
			Uq[i] = j;
	}

	/* z.U = b  (if possible) */
	for (int i = 0; i < m; i++)
		y[i] = b[i];
	bool ok = spasm_dense_forward_solve(U, y, z, Uq);

	/* y.LU = b */
	spasm_dense_back_solve(L, z, x, fact->p);
	
	free(y);
	free(z);
	free(Uq);
	return ok;
}

/* Solve XA == B (returns garbage if a solution does not exist).
 * If ok != NULL, then sets ok[i] == 1 iff xA == B[i] has a solution
 */
struct spasm_csr * spasm_gesv(const struct spasm_lu *fact, const struct spasm_csr *B, bool *ok)
{
	i64 prime = B->field->p;
	assert(prime == fact->L->field->p);
	assert(fact->L != NULL);
	int n = B->n;
	int m = B->m;
	int Xm = fact->L->n;
	struct spasm_triplet *X = spasm_triplet_alloc(n, Xm, (i64) Xm * n, prime, true);
	int *Xi = X->i;
	int *Xj = X->j;
	spasm_ZZp *Xx = X->x;

	#pragma omp parallel
	{
		spasm_ZZp *b = (spasm_ZZp *) spasm_malloc(m * sizeof(*b));
		spasm_ZZp *x = (spasm_ZZp *) spasm_malloc(Xm * sizeof(*x));
		#pragma omp for schedule(dynamic)
		for (int i = 0; i < n; i++) {
			for (int j = 0; j < m; j++) 
				b[j] = 0;
			spasm_scatter(B, i, 1, b);
			bool res = spasm_solve(fact, b, x);
			if (ok)
				ok[i] = res;
			for (int j = 0; j < Xm; j++) 
				if (x[j] != 0) {
					i64 xnz;
					#pragma omp atomic capture
					{ xnz = X->nz; X->nz += 1; }
					Xi[xnz] = i;
					Xj[xnz] = j;
					Xx[xnz] = x[j];
				}
		}
		free(b);
		free(x);
	}
	struct spasm_csr *XX = spasm_compress(X);
	spasm_triplet_free(X);
	return XX;
}

// end of spasm-master/src/spasm_solve.c

#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <argp.h>
#include <err.h>
#include <vector>

void spasm_csr_save(const struct spasm_csr *A, int * ans, std::vector<int> &nnz_idx)
{
	const int *Aj = A->j;
	const i64 *Ap = A->p;
	const spasm_ZZp *Ax = A->x;
	int n = A->n;
	int m = A->m;

	printf("%d %d M\n", n, m);
	for (int i = 0; i < n; i++)
		for (i64 px = Ap[i]; px < Ap[i + 1]; px++) {
			i64 x = (Ax != NULL) ? Ax[px] : 1;
			// printf("%d %d %" PRId64 "\n", i + 1, Aj[px] + 1, x);
			// printf("%d %d %" PRId64 "\n", i, Aj[px], x);
			i64 y = x;
			if (y < 0) y += 3;
			ans[nnz_idx[Aj[px]]] = y;
		}
	// printf("0 0 0\n");
}

struct SparseMatrix {
    int n;
    std::vector<int> row;
    std::vector<int> col;
    std::vector<uint8_t> val;
};

inline size_t idx(int i, int j, int n) { return i * n + j; }

void init_matrix(int *m, SparseMatrix &A, std::vector<uint8_t> &b, std::vector<int> &nnz_idx, int n1, int n2) {

	std::vector<int> idx2nnzidx(n1 * n2, -1);	
	
    for (int i = 0; i < n1 * n2; i++) {
		if (m[i] == 0) continue;
        b[i] = 3 - m[i];
		nnz_idx.push_back(i);
		idx2nnzidx[i] = nnz_idx.size() - 1;
    }

    for (int i = 0; i < n2; i++) {
        for (int j = 0; j < n1; j++) {
            int my_idx = idx(i, j, n1);

            if (m[my_idx] == 0) continue;

            A.row.push_back(idx2nnzidx[my_idx]);
            A.col.push_back(idx2nnzidx[my_idx]);
            A.val.push_back(1);
            // A.row.push_back(my_idx);
            // A.col.push_back(my_idx);
            // A.val.push_back(1);

            if (i > 0 && m[idx(i - 1, j, n1)] != 0) {
                A.row.push_back(idx2nnzidx[my_idx]);
                A.col.push_back(idx2nnzidx[idx(i - 1, j, n1)]);
                A.val.push_back(1);
            }

            if (i < n2 - 1 && m[idx(i + 1, j, n1)] != 0) {
                A.row.push_back(idx2nnzidx[my_idx]);
                A.col.push_back(idx2nnzidx[idx(i + 1, j, n1)]);
                A.val.push_back(1);
            }

            if (j > 0 && m[idx(i, j - 1, n1)] != 0) {
                A.row.push_back(idx2nnzidx[my_idx]);
                A.col.push_back(idx2nnzidx[idx(i, j - 1, n1)]);
                A.val.push_back(1);
            }

            if (j < n1 - 1 && m[idx(i, j + 1, n1)] != 0) {
                A.row.push_back(idx2nnzidx[my_idx]);
                A.col.push_back(idx2nnzidx[idx(i, j + 1, n1)]);
                A.val.push_back(1);
            }
        }
    }


}


/** solve several sparse linear systems */
int main(int argc, char **argv)
{

	FILE *input_file = fopen("in.data", "rb");

    int n1;
    int n2;

    fread(&n1, 1, sizeof(n1), input_file);
    fread(&n2, 1, sizeof(n2), input_file);

    int *matrix = (int *)malloc(sizeof(int) * n1 * n2);
    int *ans = (int *)malloc(sizeof(int) * n1 * n2);

    fprintf(stderr, "n1 = %zu, n2 = %zu\n", n1, n2);

    printf("Begin Reading...\n");

    fread(matrix, 1, sizeof(int) * n1 * n2, input_file);

    fclose(input_file);

	int N = n1 * n2;

	SparseMatrix my_A;
	my_A.n = n1 * n2;
    my_A.row.clear();
    my_A.col.clear();
    my_A.val.clear();
	std::vector<uint8_t> my_B(my_A.n, 0);

	std::vector<int> nnz_idx;

	init_matrix(matrix, my_A, my_B, nnz_idx, n1, n2);

	int new_N = nnz_idx.size();
	int nnz = my_A.row.size();

	printf("new_N = %d, nnz = %d\n", new_N, nnz);

	// for (int i = 0; i < new_N; i++) {
	// 	printf("nnz_idx[%d] = %d\n", i, nnz_idx[i]);
	// }


	fprintf(stderr, "Loading A\n");
	struct spasm_triplet *T = spasm_triplet_alloc(new_N, new_N, nnz, 3, true);

	for (int i = 0; i < nnz; i++) {
		spasm_add_entry(T, my_A.row[i], my_A.col[i], my_A.val[i]);
		// printf("A[%d][%d] = %d\n", my_A.row[i], my_A.col[i], my_A.val[i]);
	}
	// spasm_add_entry(T, 0, 0, 1);
	// spasm_add_entry(T, 1, 1, 1);
	// spasm_add_entry(T, 2, 2, 1);
	struct spasm_csr *A = spasm_compress(T);
	spasm_triplet_free(T);
	int n = A->n;
	int m = A->m;

	fprintf(stderr, "Loading B\n");


	int nnz_B = 0;
	for (int i = 0; i < new_N; i++) {
		if (my_B[nnz_idx[i]] != 0) {
			nnz_B++;
		}
	}

	auto TT = spasm_triplet_alloc(1, new_N, nnz_B, 3, true);
	// spasm_add_entry(TT, 0, 0, 1);
	// spasm_add_entry(TT, 0, 1, 2);
	// spasm_add_entry(TT, 0, 2, 0);
	for (int i = 0; i < new_N; i++) {
		if (my_B[nnz_idx[i]] != 0) {
			spasm_add_entry(TT, 0, i, my_B[nnz_idx[i]]);
			// printf("B[%d] = %d\n", i, my_B[nnz_idx[i]]);
		}
	}
	struct spasm_csr *B = spasm_compress(TT);
	spasm_triplet_free(TT);

	/* echelonize A */
	fprintf(stderr, "Echelonizing A\n");
	char hnnz[8];
	spasm_human_format(spasm_nnz(A), hnnz);
	fprintf(stderr, "start. A is %d x %d (%s nnz)\n", n, m, hnnz);
	struct echelonize_opts opts;
	// args.opts.L = 1;
	opts.L = 1;
	opts.enable_GPLU = true;
	double start_time = spasm_wtime();
	struct spasm_lu *fact = spasm_echelonize(A, &opts);
	// struct spasm_lu *fact = spasm_echelonize(A, NULL);
	double end_time = spasm_wtime();
	fprintf(stderr, "echelonization done in %.3f s rank = %d\n", end_time - start_time, fact->U->n);
	
	fprintf(stderr, "Solving XA == B\n");
	bool *ok = (bool *) spasm_malloc(B->n * sizeof(*ok));
	struct spasm_csr *X = spasm_gesv(fact, B, ok);
	for (int i = 0; i < B->n; i++)
		if (!ok[i])
			fprintf(stderr, "WARNING: no solution for row %d\n", i);
	fprintf(stderr, "done\n");

	// FILE *f = open_output(args.output_filename);
	// spasm_csr_save(X, f);


	spasm_csr_save(X, ans, nnz_idx);

	// printf("Begin Testing...\n");
    // auto start_time = omp_get_wtime();
    // get_ans(matrix, ans, n1, n2);
    // auto end_time = omp_get_wtime();
    // printf("Total Time: %lf seconds\n", end_time - start_time);

	FILE *output_file = fopen("out.data", "w");
    fwrite(ans, 1, sizeof(int) * n1 * n2, output_file);
    fclose(output_file);

	
	free(ans);
    free(matrix);

    return 0;


	// exit(EXIT_SUCCESS);
}


