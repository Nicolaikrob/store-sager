from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import torch.nn as nn
import torch
import matplotlib.pyplot as plt

# step 1: import MNIST+dataloader       done

# step 2: lav model

# step 3: loss func

# step 4: optimiser

# step 5: træning

# step 6: evaluation


# Set up input

traindataset = datasets.MNIST(
    root = "./data",
    train = True,
    download = True,
    transform = transforms.ToTensor()
)

trainloader = DataLoader(traindataset, 32, shuffle=True)

batch1 = next(iter(trainloader))    # Tuple(input, labels)
input = batch1[0]                   # shape(32,1,28,28)
labels = batch1[1]                  # shape(32,)
# print("billeder:", input.shape)     # giver data information om billeder
# print("labels:", labels.shape)

testdataset = datasets.MNIST(
    root = "./data",
    train = False,
    download = True,
    transform = transforms.ToTensor()
)

testloader = DataLoader(testdataset, 32, shuffle=True)


# Model

class mnistclassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Flatten(),
            nn.Linear(28*28, 32, bias=True),
            nn.ReLU(),
            nn.Linear(32, 32, bias=True),
            nn.ReLU(),
            nn.Linear(32, 10, bias=True),
        )
    
    def forward(self, inp):
        return self.layers(inp)

model = mnistclassifier()

lossfunc = nn.CrossEntropyLoss()

optimiser = torch.optim.Adam(model.parameters(), lr=0.02)

epochs = 4

train_mistakes = []
test_mistakes = []
train_loss = []
test_loss = []

totaltestloss = 0
correct = 0
for inp, label in testloader:
    with torch.no_grad():
        out = model(inp)
        loss = lossfunc(out, label)
        totaltestloss += loss.item()
    for j in range(len(label)):
        correct += int(torch.argmax(out[j]).item() == label[j].item())
    
print("Test:", totaltestloss/len(testloader))
print("Test accuracy:", f"{100*correct/len(testdataset):.2f}%")



for i in range(epochs):
    totalloss = 0
    correct = 0
    for inp, label in trainloader:
        optimiser.zero_grad()
        out = model(inp)
        loss = lossfunc(out, label)
        totalloss += loss.item()

        for j in range(len(label)):
            correct += int(torch.argmax(out[j]).item() == label[j].item())
        loss.backward()
        optimiser.step()
    
    # print("Train:", totalloss/len(trainloader))
    # print("Train accuracy:", f"{100*correct/len(traindataset):.2f}%")
    # train_mistakes.append(len(traindataset)-correct)
    train_loss.append(totalloss/len(trainloader))
    
    totaltestloss = 0
    correct = 0
    for inp, label in testloader:
        with torch.no_grad():
            out = model(inp)
            loss = lossfunc(out, label)
            totaltestloss += loss.item()
        for j in range(len(label)):
            correct += int(torch.argmax(out[j]).item() == label[j].item())
    
    print("Test:", totaltestloss/len(testloader))
    print("Test accuracy:", f"{100*correct/len(testdataset):.2f}%")
    # test_mistakes.append(len(testdataset)-correct)
    test_loss.append(totaltestloss/len(testloader))


x = range(epochs)

plt.plot(x, train_loss, marker='o', label='Train')
plt.plot(x, test_loss, marker='o', label='Test')

plt.legend()
plt.savefig("plot.png")