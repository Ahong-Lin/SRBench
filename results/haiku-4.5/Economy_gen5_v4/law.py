def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts the output variable based on the input variables according to a discovered law.

    Args:
        input_data: A list of dictionaries, where each dictionary is a single data
                    point containing the input variable names
                    ('dc', 'pi', 'dp_comp', 'sigma_c', 'dc_acc') as keys and their
                    corresponding values.

    Returns:
        A list of dictionaries, corresponding to the input_data list, with each
        dictionary containing the predicted output variable, e.g. {"dp": value}.
    """
    results = []

    # Polynomial degree 3 Ridge regression formula with R² = 0.9940
    for data_point in input_data:
        dc = data_point.get('dc', 0)
        pi = data_point.get('pi', 0)
        dp_comp = data_point.get('dp_comp', 0)
        sigma_c = data_point.get('sigma_c', 0)
        dc_acc = data_point.get('dc_acc', 0)

        dp = (0.1987578604 * dp_comp +
              0.1908315662 * dc * pi +
              0.1742458363 * dc_acc +
              0.1153282822 * dc +
              0.0761442874 * dc**3 -
              0.0529581704 * dc * pi**2 -
              0.0426481752 * dp_comp**3 -
              0.0360650659 * dc * sigma_c -
              0.0340714206 * pi**2 +
              0.0310364699 * dc**2 -
              0.0245297628 * pi * dp_comp +
              0.0217746856 * pi -
              0.0206122174 * dc_acc**3 +
              0.0186889130 * pi**2 * dp_comp +
              0.0168546803 * pi**3 +
              0.0164434694 * dc * pi * sigma_c -
              0.0136655726 * dp_comp**2 * sigma_c +
              0.0132685281 * dc**2 * pi +
              0.0084217870 * sigma_c -
              0.0078364259 * sigma_c**2 -
              0.0071700253 * pi * sigma_c +
              0.0068178938 * pi * sigma_c * dc_acc +
              0.0066890629 * dp_comp**2 +
              0.0064910100 * sigma_c**3 +
              0.0064691941 * pi * sigma_c**2 -
              0.0063337708 * sigma_c * dc_acc +
              0.0043246855 * pi * dp_comp * sigma_c -
              0.0042199549 * dc**2 * sigma_c -
              0.0036027361 * dp_comp * dc_acc +
              0.0035141029 * pi * dp_comp * dc_acc +
              0.0033750754 * pi**2 * sigma_c -
              0.0023102500 * pi * dc_acc +
              0.0022194928 * dp_comp * sigma_c**2 +
              0.0020426519 * dc * sigma_c**2 -
              0.0020353112 * dc * pi * dp_comp +
              0.0018335616 * dp_comp**2 * dc_acc +
              0.0015610302 * sigma_c**2 * dc_acc +
              0.0015491711 * dp_comp * sigma_c * dc_acc +
              0.0014199966 * dp_comp * sigma_c -
              0.0009173998 * pi * dp_comp**2 +
              0.0008832111 * pi * dc_acc**2 +
              0.0007116221 * dc * sigma_c * dc_acc +
              0.0007058901 * dc * dp_comp -
              0.0005343147 * dc_acc**2 -
              0.0005055380 * pi**2 * dc_acc +
              0.0005049215 * dc * pi * dc_acc -
              0.0004130336 * dc**2 * dp_comp -
              0.0003062779 * dc * dp_comp**2 +
              0.0002523816 * dc * dc_acc**2 +
              0.0002301185 * dc * dp_comp * sigma_c -
              0.0002162656 * dc**2 * dc_acc -
              0.0001960536 * dc * dc_acc -
              0.0001844215 * dc * dp_comp * dc_acc +
              0.0001410804 * dp_comp * dc_acc**2 -
              0.0001056320 * sigma_c * dc_acc**2)

        results.append({"dp": dp})

    return results
