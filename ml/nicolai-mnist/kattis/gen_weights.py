

W = [[1 if i%2==0 else -1]*51 for i in range(30)]

with open("mnist2_weights.txt", "w") as f:
    for R in W:
        for e in R: f.write(f"{e} ")
        f.write('\n')