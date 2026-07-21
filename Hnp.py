import random

# Use a smaller prime order 'n' for demonstration to keep matrix math fast
# Real Bitcoin uses secp256k1's order: 115792089237316195423570985008687907852837564279074904382605163141518161494337
N = 1000000000000037  # A large prime for illustration
BITS_LEAKED = 4       # Number of top bits leaked from the nonce

def generate_hnp_instance(private_key, num_signatures):
    """Simulates a side-channel attack collecting signatures with leaked nonce bits."""
    instances = []
    # Max bound of the unknown error part 'e'
    error_bound = N // (2**BITS_LEAKED)
    
    for _ in range(num_signatures):
        z = random.randint(1, N - 1)      # Tx Hash
        k = random.randint(1, N - 1)      # Nonce
        
        # Split nonce into known high bits (alpha) and unknown low bits (error)
        alpha = (k >> (k.bit_length() - BITS_LEAKED)) << (k.bit_length() - BITS_LEAKED)
        error = k - alpha
        
        # Calculate mock ECDSA signature parts
        r = random.randint(1, N - 1)
        s = (pow(k, -1, N) * (z + r * private_key)) % N
        
        # Rearrange to match HNP format: t * d - u = error (mod n)
        s_inv = pow(s, -1, N)
        t = (r * s_inv) % N
        u = (alpha - (z * s_inv)) % N
        
        instances.append((t, u))
        
    return instances, error_bound

def solve_hnp_lattice(instances, error_bound):
    """
    Constructs an HNP matrix. In a real environment, 
    you pass this matrix directly to an LLL algorithm (like in SageMath).
    """
    m = len(instances)
    
    # Building an (m+2) x (m+2) embedding matrix
    # Rows represent the modular relations of our signatures
    matrix = [[0] * (m + 2) for _ in range(m + 2)]
    
    for i in range(m):
        matrix[i][i] = N
        matrix[m][i] = instances[i][0]   # t_i values
        matrix[m+1][i] = instances[i][1] # u_i values
        
    # Scale elements to balance weights for the shortest vector search
    matrix[m][m] = error_bound / N
    matrix[m+1][m+1] = error_bound
    
    print(f"Generated {m}x{m} Lattice Matrix successfully.")
    print("In production environments, running LLL or BKZ reduction on this")
    print("matrix pulls the private key 'd' directly out of the shortest vector.")
    return matrix

# --- Execution ---
SECRET_PRIVATE_KEY = 1234567891011
signature_data, bound = generate_hnp_instance(SECRET_PRIVATE_KEY, num_signatures=5)
lattice_matrix = solve_hnp_lattice(signature_data, bound)
