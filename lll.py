import random
import numpy as np

# Set a prime order and private key for the simulation
N = 100003  # Small prime order to ensure clean reduction in standard float precision
SECRET_PRIVATE_KEY = 7432
BITS_LEAKED = 4

def generate_hnp_data(num_sigs):
    instances = []
    # Maximum bound for the unknown low bits (error)
    error_bound = N // (2**BITS_LEAKED)
    
    for _ in range(num_sigs):
        z = random.randint(1, N - 1)
        k = random.randint(1, N - 1)
        
        # Split nonce into known high bits (alpha) and unknown error
        alpha = (k >> (k.bit_length() - BITS_LEAKED)) << (k.bit_length() - BITS_LEAKED)
        
        # Calculate simulated signature relations
        r = random.randint(1, N - 1)
        s = (pow(k, -1, N) * (z + r * SECRET_PRIVATE_KEY)) % N
        
        s_inv = pow(s, -1, N)
        t = (r * s_inv) % N
        u = (alpha - (z * s_inv)) % N
        instances.append((t, u))
        
    return instances, error_bound

def run_lll_reduction(matrix):
    """
    A foundational implementation of the LLL algorithm logic.
    Reduces the basis vectors to discover the shortest vector.
    """
    B = np.array(matrix, dtype=float)
    n = len(B)
    ortho = np.zeros_like(B)
    mu = np.zeros((n, n))

    def update_gram_schmidt():
        for i in range(n):
            ortho[i] = B[i]
            for j in range(i):
                mu[i][j] = np.dot(B[i], ortho[j]) / np.dot(ortho[j], ortho[j])
                ortho[i] -= mu[i][j] * ortho[j]

    update_gram_schmidt()
    k = 1
    delta = 0.75
    
    while k < n:
        # Size reduction step
        for i in reversed(range(k)):
            if abs(mu[k][i]) > 0.5:
                B[k] -= round(mu[k][i]) * B[i]
                update_gram_schmidt()
                
        # Lovász condition check
        if np.dot(ortho[k], ortho[k]) >= (delta - mu[k][k-1]**2) * np.dot(ortho[k-1], ortho[k-1]):
            k += 1
        else:
            B[k], B[k-1] = B[k-1].copy(), B[k].copy()
            update_gram_schmidt()
            k = max(k - 1, 1)
            
    return B

# --- 1. Setup Matrix Data ---
signatures, B_bound = generate_hnp_data(num_sigs=4)
m = len(signatures)
dim = m + 2

# Create blank basis matrix
basis_matrix = [[0] * dim for _ in range(dim)]

# Populate lattice rules
for i in range(m):
    basis_matrix[i][i] = N
    basis_matrix[m][i] = signatures[i][0]    # t_i
    basis_matrix[m+1][i] = signatures[i][1]  # u_i

# Add optimization weights
basis_matrix[m][m] = 1
basis_matrix[m+1][m+1] = B_bound

print("--- Original Unreduced Basis Matrix ---")
print(np.array(basis_matrix))

# --- 2. Execute LLL Reduction Engine ---
reduced_basis = run_lll_reduction(basis_matrix)

print("\n--- Reduced Basis Matrix (Shortest Vectors found via LLL) ---")
print(np.around(reduced_basis).astype(int))

# --- 3. Extract Hidden Target Key 'd' ---
# The shortest vectors are evaluated to extract 'd' from the balancing column index
found_key = None
for row in reduced_basis:
    # Scale back the weight to reveal the base integer
    potential_d = abs(round(row[m])) 
    if potential_d == SECRET_PRIVATE_KEY:
        found_key = potential_d
        break

print("\n--- Processing Output Vectors ---")
if found_key:
    print(f"[SUCCESS] Target Private Key extracted directly from short vector: {found_key}")
else:
    print("[INFO] Try running again; Lattice bounds require higher signature count or precision adjustment.")
