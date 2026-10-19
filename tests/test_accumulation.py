"""Gradyan biriktirme: batch_size x accum_steps, aynı etkin batch'le tek büyük batch'e eşdeğer olmalı.

- Optimizer SGD: Adam'ın ilk adımı gradyan ölçeğinden bağımsızdır (≈ lr * sign(g)); kaybın
  accum_steps'e bölünmesi unutulsa bile AdamW'li test geçerdi.
- convnext_tiny'nin stochastic depth'i kapatılır: rastgele blok düşürme micro-batch'lere farklı
  rastgelelik uygular. convnext LayerNorm kullanır, yani BatchNorm'daki batch bağımlılığı yok.
- Augmentation yok: girdi sabit, sentetik tensörler (KIDO gerekmez). CPU, float32.
"""
import copy
import unittest

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from torchvision.ops import StochasticDepth

from src.training import build_model, train_epoch

SEED, SIZE, LR = 42, 64, 0.1


def updates_after_epoch(model, data, batch_size, accum_steps):
    # Modelin kopyasını verilen batch/accum ile bir epoch eğitir; ağırlık değişimlerini döndürür
    m = copy.deepcopy(model)
    m.train()
    optim = torch.optim.SGD(m.parameters(), lr=LR)
    scaler = torch.amp.GradScaler("cuda", enabled=False)
    loader = DataLoader(data, batch_size=batch_size, shuffle=False)
    train_epoch(m, loader, optim, scaler, nn.CrossEntropyLoss(label_smoothing=0.1), accum_steps)
    return [(p1 - p0).detach() for p1, p0 in zip(m.parameters(), model.parameters())]


class AccumulationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.manual_seed(SEED)
        cls.model = build_model("convnext_tiny", pretrained=False).cpu()
        for mod in cls.model.modules():
            if isinstance(mod, StochasticDepth):
                mod.p = 0.0
        g = torch.Generator().manual_seed(SEED)
        cls.x = torch.randn(48, 3, SIZE, SIZE, generator=g)
        cls.y = torch.randint(0, 2, (48,), generator=g)

    def assert_same(self, a, b):
        for da, db in zip(a, b):
            torch.testing.assert_close(da, db, rtol=1e-3, atol=1e-6)

    def test_single_step(self):
        # 32 görsel: 32 x 1 tek adım, 16 x 2 de tek adım
        data = TensorDataset(self.x[:32], self.y[:32])
        self.assert_same(updates_after_epoch(self.model, data, 32, 1), updates_after_epoch(self.model, data, 16, 2))

    def test_partial_group(self):
        # 48 görsel: 32 x 1 -> 32 + 16; 16 x 2 -> (16, 16) + yarım grup (16). Yarım grup kendi boyuna bölünmeli.
        data = TensorDataset(self.x, self.y)
        self.assert_same(updates_after_epoch(self.model, data, 32, 1), updates_after_epoch(self.model, data, 16, 2))

    def test_detects_missing_division(self):
        # Testin duyarlılığı: accum'suz 16'lık iki adım (bölme yok, iki ayrı adım) 32 x 1'den farklı olmalı
        data = TensorDataset(self.x[:32], self.y[:32])
        with self.assertRaises(AssertionError):
            self.assert_same(updates_after_epoch(self.model, data, 32, 1), updates_after_epoch(self.model, data, 16, 1))


if __name__ == "__main__":
    unittest.main()
