import math

# Discovered relationship (GHK / Nernst-type logarithmic law):
#   Vm = A * ln(Co + B) + C
# Fitted on /app/data/train_data.csv (clean Vm), RMSE ~2.0e-4 V.
A = 0.031574105715541576
B = 6.109313837111925
C = -0.14873033899060292


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    row = input_data[0]
    Co = row["Co"]
    Vm = A * math.log(Co + B) + C
    return [{"Vm": Vm}]
