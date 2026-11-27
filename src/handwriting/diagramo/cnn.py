"""Model B: önceden eğitilmiş hafif CNN (ResNet18, ImageNet) ile **sabit gömme** + ordinal baş. CNN eğitilmez/ince ayar yapılmaz.

Görüntüler yeniden boyutlandırılmaz (tablet tuvali 1393 x 813 px, 4 px/tb ya da kırpılmış görüntü yerel boyutta); ağ tam evrişimlidir ve son katman haritasının
global ortalama + global maksimum havuzlaması (512 + 512 = 1024 boyut) alınır. Veri artırma yok. Gömme çıkarma etiketleri kullanmaz (sızıntı yok); PCA ve ölçekleme yalnız eğitim katlarında öğrenilir.
"""
import numpy as np
import pandas as pd
import torch
import torchvision
from PIL import Image
from sklearn.decomposition import PCA
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .io import ROOT
from .models import OrdinalLogit, metrics

MEAN, STD = np.array([0.485, 0.456, 0.406], np.float32), np.array([0.229, 0.224, 0.225], np.float32)


def embed(names, variant="tablet", device=None, cache=True):
    """Her görüntü için 1024 boyutlu gömme (avg + max havuzlama). Önbellek: processed/embeddings_<variant>.npz (yerel)."""
    f = ROOT / "processed" / f"embeddings_{variant}.npz"
    if cache and f.exists():
        z = np.load(f, allow_pickle=True)
        if list(z["names"]) == list(names):
            return z["emb"]
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    net = torchvision.models.resnet18(weights=torchvision.models.ResNet18_Weights.DEFAULT)
    body = torch.nn.Sequential(*list(net.children())[:-2]).to(device).eval()
    out = []
    with torch.no_grad():
        for n in names:
            a = np.asarray(Image.open(ROOT / "processed" / "images" / variant / n).convert("L"), np.float32) / 255.0
            x = (np.stack([a] * 3, 0) - MEAN[:, None, None]) / STD[:, None, None]
            fm = body(torch.from_numpy(x)[None].to(device))
            out.append(torch.cat([fm.mean((2, 3)), fm.amax((2, 3))], 1).cpu().numpy()[0])
    emb = np.vstack(out)
    if cache:
        np.savez_compressed(f, emb=emb, names=np.array(list(names)))
    return emb


def fit_predict_emb(n_pca, C, Etr, ytr, ctr, Ete, cte):
    """Gömme → standartlaştırma → PCA(n_pca) → (+ görev türü) → ordinal lojistik. Döner: sürekli tahmin."""
    pre = make_pipeline(StandardScaler(), PCA(n_components=n_pca, random_state=0))
    Ztr = pre.fit_transform(Etr); Zte = pre.transform(Ete)
    sd = Ztr.std(0) + 1e-9
    Ztr, Zte = Ztr / sd, Zte / sd
    Ztr = np.c_[Ztr, ctr]; Zte = np.c_[Zte, cte]
    return OrdinalLogit(C=C).fit(Ztr, ytr).predict_cont(Zte)


EMB_CONFIGS = [(v, n, C) for v in ("tablet", "crop") for n in (16, 32, 64) for C in (0.03, 0.1)]


def development_table_emb(d, embs, targets=("layout", "letter", "alter"), k=5):
    """embs: {variant: (n_kayıt, 1024)}, d ile aynı sıra. CV(train, okul-gruplu) + val; test kullanılmaz."""
    rows = []
    tr_idx, va_idx = np.flatnonzero(d.bolum == "train"), np.flatnonzero(d.bolum == "val")
    for t in targets:
        for v, n, C in EMB_CONFIGS:
            E = embs[v]
            a_idx = tr_idx[d.iloc[tr_idx][t].notna().values]; b_idx = va_idx[d.iloc[va_idx][t].notna().values]
            oof = np.full(len(a_idx), np.nan); fold_q = []
            for tr, te in GroupKFold(k).split(a_idx, groups=d.iloc[a_idx].school):
                i, j = a_idx[tr], a_idx[te]
                c = fit_predict_emb(n, C, E[i], d.iloc[i][t].values, d.iloc[i].is_copy.values, E[j], d.iloc[j].is_copy.values)
                oof[te] = c; fold_q.append(metrics(d.iloc[j][t].values, c)["qwk"])
            cv = metrics(d.iloc[a_idx][t].values, oof)
            c = fit_predict_emb(n, C, E[a_idx], d.iloc[a_idx][t].values, d.iloc[a_idx].is_copy.values, E[b_idx], d.iloc[b_idx].is_copy.values)
            vm = metrics(d.iloc[b_idx][t].values, c)
            rows.append(dict(hedef=t, config=f"B_{v}_pca{n}_C{C}", cv_mae=cv["mae"], cv_qwk=cv["qwk"], cv_spearman=cv["spearman"], cv_qwk_fold_mean=float(np.mean(fold_q)), cv_qwk_fold_sd=float(np.std(fold_q)),
                             val_mae=vm["mae"], val_qwk=vm["qwk"], val_spearman=vm["spearman"], n_ozellik=n, n_train=len(a_idx), n_val=len(b_idx)))
    r = pd.DataFrame(rows)
    r["secim_puani"] = (r.cv_qwk + r.val_qwk) / 2
    return r


def final_test_emb(d, embs, chosen):
    """Seçilen gömme yapılandırmaları train+val'de eğitilir, test'te bir kez değerlendirilir. Kilit varsa hata verir (kilidi `models.final_test` yazar; ikisi aynı olayda: önce bu, sonra o).
    chosen: {hedef: (variant, n_pca, C)}."""
    from .models import LOCK, cluster_ci
    if LOCK.exists():
        raise RuntimeError(f"Test kümesi zaten kullanıldı ({LOCK.name}); yeniden kullanım yalnız kullanıcı kararıyla.")
    dev_idx, te_idx = np.flatnonzero(d.bolum.isin(["train", "val"])), np.flatnonzero(d.bolum == "test")
    out, preds = [], {}
    for t, (v, n, C) in chosen.items():
        a = dev_idx[d.iloc[dev_idx][t].notna().values]; b = te_idx[d.iloc[te_idx][t].notna().values]
        E = embs[v]
        c = fit_predict_emb(n, C, E[a], d.iloc[a][t].values, d.iloc[a].is_copy.values, E[b], d.iloc[b].is_copy.values)
        m = metrics(d.iloc[b][t].values, c)
        ci_q = cluster_ci(d.iloc[b][t].values, c, d.iloc[b].school.values, lambda y, x: metrics(y, x)["qwk"])
        ci_m = cluster_ci(d.iloc[b][t].values, c, d.iloc[b].school.values, lambda y, x: metrics(y, x)["mae"])
        out.append(dict(hedef=t, config=f"B_{v}_pca{n}_C{C}", n=len(b), mae=m["mae"], mae_ci_lo=ci_m[0], mae_ci_hi=ci_m[1], qwk=m["qwk"], qwk_ci_lo=ci_q[0], qwk_ci_hi=ci_q[1], spearman=m["spearman"]))
        preds[t] = dict(cont=np.asarray(c).tolist(), images=d.iloc[b].image.tolist())
    return pd.DataFrame(out), preds
