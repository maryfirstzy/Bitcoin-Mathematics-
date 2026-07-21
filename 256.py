import random
from sympy import Matrix

# Real 256-bit secp256k1 order
N = 115792089237316195423570985008687907852837564279074904382605163141518161494337
SECRET_PRIVATE_KEY = 9876543210123456789012345678901234567890  # 256-bit private key
BITS_LEAKED = 8
NUM_SIGNATURES = 30  # Larger leak requires fewer dimensions to resolve

def generate_256bit_data():
    instances = []
    error_bound = N // (2**BITS_LEAKED)
    
    for _ in range(NUM_SIGNATURES):
        z = random.randint(1, N - 1)
        k = random.randint(1, N - 1)
        
        # Split 256-bit nonce into known high bits and error
        alpha = (k >> (k.bit_length() - BITS_LEAKED)) << (k.bit_length() - BITS_LEAKED)
        
        r = random.randint(1, N - 1)
        s = (pow(k, -1, N) * (z + r * SECRET_PRIVATE_KEY)) % N
        
        s_inv = pow(s, -1, N)
        t = (r * s_inv) % N
        u = (alpha - (z * s_inv)) % N
        instances.append((t, u))
        
    return instances, error_bound

# 1. Setup 256-bit Data
signatures, B_bound = generate_256bit_data()
dim = NUM_SIGNATURES + 2

# 2. Build Python list matrix structure
raw_matrix = [[0] * dim for _ in range(dim)]
for i in range(NUM_SIGNATURES):
    raw_matrix[i][i] = N
    raw_matrix[NUM_SIGNATURES][i] = signatures[i][0]
    raw_matrix[NUM_SIGNATURES + 1][i] = signatures[i][1]

raw_matrix[NUM_SIGNATURES][NUM_SIGNATURES] = 1
raw_matrix[NUM_SIGNATURES + 1][NUM_SIGNATURES + 1] = B_bound

print(f"Initializing {dim}x{dim} arbitrary-precision SymPy matrix...")
sympy_matrix = Matrix(raw_matrix)

# 3. Run LLL orthogonalization logic on the high-dimensional matrix
print("Reducing matrix (this handles 256-bit integers natively)...")
reduced_basis = sympy_matrix.LLL()

# 4. Parse the output rows for the key
found = False
for row in reduced_basis.tolist():
    potential_d = abs(row[NUM_SIGNATURES])
    if potential_d == SECRET_PRIVATE_KEY:
        print(f"\n[SUCCESS] Extracted full 256-bit key: {potential_d}")
        found = True
        break

if not found:
    print("\n[INFO] Lattice reduction completed, but shortest vector path was unaligned. Try increasing NUM_SIGNATURES.")
