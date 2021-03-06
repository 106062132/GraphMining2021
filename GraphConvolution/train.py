import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import dgl
from dgl.data import register_data_args

from gcn import GCN

class arguments():
    def __init__(self):
        self.lr = 0.0005
        self.epochs = 3000

def evaluate(model, g, features, labels, mask):
    model.eval()
    with torch.no_grad():
        logits = model(g, features)
        logits = logits[mask]
        labels = labels[mask]
        _, indices = torch.max(logits, dim=1)
        correct = torch.sum(indices == labels)
        return correct.item() * 1.0 / len(labels)

def main():
    # data from dgl
    (g,), _  = dgl.load_graphs("graph.dgl")
    g = g.int().to(0)
    
    features = g.ndata['feat']
    labels = g.ndata['label']
    train_mask = g.ndata['train_mask'].bool()
    val_mask = g.ndata['val_mask'].bool()
    test_mask = g.ndata['test_mask'].bool()
    in_feats = features.shape[1]
    n_classes = len(torch.unique(labels))
    
    # add self loop
    g = dgl.remove_self_loop(g)
    g = dgl.add_self_loop(g)
    
    args = arguments()
    # create GCN model
    model = GCN(in_feats, n_classes)
    model.cuda()
    loss_fcn = torch.nn.CrossEntropyLoss()
    
    # use optimizer
    optimizer = torch.optim.Adam(model.parameters(),
                                 lr=args.lr,
                                 weight_decay=0.0005)
        
    # initialize graph
    for epoch in range(args.epochs):
        model.train()
        # forward
        logits = model(g, features)
        loss = loss_fcn(logits[train_mask], labels[train_mask])

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        acc = evaluate(model, g, features, labels, val_mask)
        print("Epoch {:05d} | Loss {:.4f} | Accuracy {:.4f} | ". format(epoch, loss.item(), acc))

    acc = evaluate(model, g, features, labels, test_mask)
    print("Test accuracy {:.2%}".format(acc))


if __name__ == '__main__':
    main()
