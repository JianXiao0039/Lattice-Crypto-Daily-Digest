# Phase 14B Terminology Stability Review

Status: `terminology_stability_ready`.

The implementation adds `TERMINOLOGY_TABLE` in `src/lattice_digest/recommendation_rationale.py`.

Checked terms include:

- Learning With Errors（LWE）;
- Ring-LWE（RLWE）;
- Module-LWE（MLWE）;
- Short Integer Solution（SIS）;
- Module-SIS;
- BKZ;
- ML-KEM;
- ML-DSA;
- 全同态加密（FHE）;
- CKKS;
- 零知识证明（ZKP）;
- chameleon hash / 变色龙哈希.

The regression tests reject awkward project-inappropriate translations such as 格子密码, 学习带错误, and 戒指签名.

English rationale uses standard English cryptographic terms such as Module-LWE (MLWE), ML-KEM, BKZ, and lattice cryptography.
