import math

def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict X values using damped oscillation model with light intensity modulation.

    Model: X = (A + K*I_light)*exp(-B*t)*cos(C*t + D) + E

    Parameters (fitted from training data):
    - A = 2.010197486114329
    - K = 0.21933664607839568
    - B = 0.03423272708677376
    - C = 0.25617689336548394
    - D = -0.75011408315623
    - E = 0.07526055785589185
    """

    # Fitted parameters
    A = 2.010197486114329
    K = 0.21933664607839568
    B = 0.03423272708677376
    C = 0.25617689336548394
    D = -0.75011408315623
    E = 0.07526055785589185

    results = []

    for data_point in input_data:
        t = data_point['t']
        I_light_prev = data_point['I_light_prev']

        # Calculate X using the fitted model
        amplitude = A + K * I_light_prev
        decay = math.exp(-B * t)
        oscillation = math.cos(C * t + D)
        X = amplitude * decay * oscillation + E

        results.append({
            't': t,
            'I_light_prev': I_light_prev,
            'X': X
        })

    return results
