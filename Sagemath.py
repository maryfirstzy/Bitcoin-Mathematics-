# This script is meant to be run inside a SageMath environment (.sage)
import random

# 1. Define real secp256k1 curve prime order (256-bit)
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
SECRET_PRIVATE_KEY = 0x4a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b # Random 256-bit key
BITS_LEAKED = 4
NUM_SIGNATURES = 70  # Roughly 65-70 signatures are mathematically needed for 4-bit leaks

def generate_real_256bit_data():
    instances = []
    error_bound = N // (2**BITS_LEAKED)
    
    for _ in range(NUM_SIGNATURES):
        z = random.randint(1, N - 1)
        k = random.randint(1, N - 1)
        
        # Isolate known top bits (alpha) and unknown low bits (error)
        shift = k.bit_length() - BITS_LEAKED
        alpha = (k >> shift) << shift
        
        r = random.randint(1, N - 1)
        s = (pow(k, -1, N) * (z + r * SECRET_PRIVATE_KEY)) % N
        
        s_inv = pow(s, -1, N)
        t = (r * s_inv) % N
        u = (alpha - (z * s_inv)) % N
        instances.append((t, u))
        
    return instances, error_bound

# Generate data
signatures, B_bound = generate_real_256bit_data()
dim = NUM_SIGNATURES + 2

# 2. Construct the high-dimensional Lattice Matrix in SageMath
# We use Sage's Matrix Space with Arbitrary Precision Integers (ZZ)
M = Matrix(ZZ, dim, dim)

for i in range(NUM_SIGNATURES):
    M[i, i] = N
    M[NUM_SIGNATURES, i] = signatures[i][0]    # t_i
    M[NUM_SIGNATURES + 1, i] = signatures[i][1]  # u_i

M[NUM_SIGNATURES, NUM_SIGNATURES] = 1
M[NUM_SIGNATURES + 1, NUM_SIGNATURES + 1] = B_bound

print(f"Constructed a {dim}x{dim} 256-bit Lattice Matrix.")
print("Running LLL reduction engine...")

# 3. Execute LLL reduction using Sage's optimized backend
reduced_M = M.LLL()

print("\n--- Scanning Shortest Vectors ---")
success = False
for row in reduced_M:
    potential_key = abs(row[NUM_SIGNATURES])
    if potential_key == SECRET_PRIVATE_KEY:
        print(f"[SUCCESS] 256-bit Private Key Recovered: {hex(potential_key)}")
        success = True
        break

if not success:
    print("[INFO] Target key not found. Increase NUM_SIGNATURES slightly to bound the target tighter.")
