def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dE_dt from input variables (t, E, A, G).

    Model: dE_dt = k(A, G) * E
    where k(A, G) is a 3rd-order polynomial in A and G.
    """
    # Coefficients from fitting a 3rd-order polynomial to the training data
    c = [
        -0.1958582473,      # c0: constant
        0.0309637480,       # c1: A
        0.2280564423,       # c2: G
        0.0071235283,       # c3: A²
        -0.0200484831,      # c4: G²
        -0.0608183585,      # c5: A*G
        -0.0009341282,      # c6: A³
        0.0004545805,       # c7: G³
        0.0037493881,       # c8: A²*G
        0.0026751036        # c9: A*G²
    ]

    results = []
    for row in input_data:
        A = row['A']
        G = row['G']
        E = row['E']

        # Compute rate constant k as polynomial in A and G
        k = (c[0] + c[1]*A + c[2]*G +
             c[3]*A**2 + c[4]*G**2 + c[5]*A*G +
             c[6]*A**3 + c[7]*G**3 + c[8]*A**2*G + c[9]*A*G**2)

        # Compute dE_dt = k * E
        dE_dt = k * E

        results.append({'dE_dt': dE_dt})

    return results
