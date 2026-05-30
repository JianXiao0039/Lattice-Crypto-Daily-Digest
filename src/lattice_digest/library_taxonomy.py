from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class TaxonomyResult:
    research_tags: list[str]
    lattice_tags: list[str]
    pqc_tags: list[str]
    attack_tags: list[str]
    primitive_tags: list[str]
    implementation_tags: list[str]
    ai_tags: list[str]
    zotero_tags: list[str]
    obsidian_links: list[str]


def normalize_text(value: str) -> str:
    text = value.lower()
    text = text.replace("–", "-").replace("—", "-").replace("‑", "-")
    text = re.sub(r"[_/]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return f" {text.strip()} "


def _contains(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _add(tags: list[str], tag: str) -> None:
    if tag not in tags:
        tags.append(tag)


def _stable(tags: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(tag for tag in tags if tag))


LATTICE_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Module-SIS", (r"\bmodule[- ]sis\b", r"\bmsis\b")),
    ("Ring-SIS", (r"\bring[- ]sis\b", r"\brsis\b")),
    ("SIS", (r"\bshort integer solution\b", r"\bsis\b")),
    ("NTRU-SIS", (r"\bntru[- ]sis\b",)),
    ("NTRU", (r"\bntru\b",)),
    ("Search-LWE", (r"\bsearch[- ]lwe\b",)),
    ("Decision-LWE", (r"\bdecision[- ]lwe\b",)),
    ("Ring-LWE", (r"\bring[- ]lwe\b", r"\brlwe\b")),
    ("Module-LWE", (r"\bmodule[- ]lwe\b", r"\bmlwe\b")),
    ("Polynomial-LWE", (r"\bpolynomial[- ]lwe\b", r"\bplwe\b")),
    ("Middle-Product LWE", (r"\bmiddle[- ]product lwe\b", r"\bmplwe\b")),
    ("Sparse LWE", (r"\bsparse lwe\b",)),
    ("Binary Secret LWE", (r"\bbinary secret lwe\b",)),
    ("Ternary Secret LWE", (r"\bternary secret lwe\b",)),
    ("Small Secret LWE", (r"\bsmall secret lwe\b",)),
    ("LWE", (r"\blearning with errors\b", r"\blwe\b")),
    ("Ring-LWR", (r"\bring[- ]lwr\b",)),
    ("Module-LWR", (r"\bmodule[- ]lwr\b",)),
    ("Learning With Rounding", (r"\blearning with rounding\b", r"\blwr\b")),
    ("LPN", (r"\blearning parity with noise\b", r"\blpn\b")),
    ("SVP", (r"\bshortest vector problem\b", r"\bsvp\b")),
    ("CVP", (r"\bclosest vector problem\b", r"\bcvp\b")),
    ("BDD", (r"\bbounded distance decoding\b", r"\bbdd\b")),
    ("uSVP", (r"\bunique svp\b", r"\busvp\b")),
    ("GapSVP", (r"\bgapsvp\b", r"\bgap svp\b")),
    ("SIVP", (r"\bsivp\b", r"\bshortest independent vectors problem\b")),
    ("ISIS", (r"\binhomogeneous sis\b", r"\bisis\b")),
    ("Error Distribution", (r"\berror distribution\b", r"\bnoise distribution\b")),
    ("Discrete Gaussian", (r"\bdiscrete gaussian\b",)),
    ("Gaussian Sampling", (r"\bgaussian sampling\b",)),
    ("Trapdoor Sampling", (r"\btrapdoor sampling\b",)),
    ("Gadget Matrix", (r"\bgadget matrix\b", r"\bgadget decomposition\b")),
    ("q-ary lattice", (r"\bq[- ]ary lattice\b",)),
    ("Ideal Lattice", (r"\bideal lattice\b",)),
    ("Module Lattice", (r"\bmodule lattice\b", r"\bmodule lattices\b")),
    ("Cyclotomic Ring", (r"\bcyclotomic ring\b", r"\bcyclotomic\b")),
    ("Negacyclic Ring", (r"\bnegacyclic\b", r"\bnegative[- ]cyclic\b")),
    ("Power-of-Two Cyclotomic", (r"\b2[- ]power cyclotomic\b", r"\bpower[- ]of[- ]two cyclotomic\b")),
    ("Polynomial Quotient Ring", (r"\bpolynomial quotient ring\b", r"\bquotient ring\b")),
    ("Lattice", (r"\blattice\b", r"\blattices\b")),
]


REDUCTION_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("BKZ 2.0", (r"\bbkz 2\.0\b",)),
    ("Self-Dual BKZ", (r"\bself[- ]dual bkz\b",)),
    ("DeepBKZ", (r"\bdeepbkz\b", r"\bdeep bkz\b")),
    ("Progressive BKZ", (r"\bprogressive bkz\b",)),
    ("BKZ", (r"\bbkz\b", r"\bblock korkine[- ]zolotarev\b")),
    ("LLL", (r"\blll\b", r"\blenstra[- ]lenstra[- ]lovasz\b")),
    ("Slide Reduction", (r"\bslide reduction\b",)),
    ("Pumping", (r"\bpumping\b",)),
    ("G6K", (r"\bg6k\b",)),
    ("fplll", (r"\bfplll\b",)),
    ("fpylll", (r"\bfpylll\b",)),
    ("Enum", (r"\benum\b",)),
    ("Enumeration", (r"\benumeration\b", r"\bschnorr[- ]euchner\b")),
    ("Extreme Pruning", (r"\bextreme pruning\b",)),
    ("Pruning", (r"\bpruning\b",)),
    ("GaussSieve", (r"\bgausssieve\b", r"\bgauss sieve\b")),
    ("NV-Sieve", (r"\bnv[- ]sieve\b",)),
    ("Tuple Sieve", (r"\btuple sieve\b",)),
    ("HashSieve", (r"\bhashsieve\b", r"\bhash sieve\b")),
    ("Sieving", (r"\bsieving\b", r"\bsieve\b")),
    ("Voronoi Cell", (r"\bvoronoi cell\b", r"\bvoronoi reduction\b")),
    ("Nearest Plane", (r"\bnearest plane\b",)),
    ("Babai", (r"\bbabai\b",)),
    ("Dual Lattice", (r"\bdual lattice\b",)),
    ("Gram-Schmidt", (r"\bgram[- ]schmidt\b",)),
    ("GSO", (r"\bgso\b",)),
    ("Root Hermite Factor", (r"\broot hermite factor\b", r"\brhf\b")),
    ("Hermite Factor", (r"\bhermite factor\b",)),
    ("GSA", (r"\bgsa\b", r"\bgeometric series assumption\b")),
    ("Block Size", (r"\bblock size\b", r"\bblocksize\b")),
    ("Core-SVP", (r"\bcore[- ]svp\b",)),
    ("Cost Model", (r"\bcost model\b", r"\bcost estimate\b")),
    ("Lattice Estimator", (r"\blattice estimator\b",)),
    ("Security Estimator", (r"\bsecurity estimator\b",)),
    ("Quantum Sieve", (r"\bquantum sieve\b", r"\bquantum sieving\b")),
    ("Classical Cost", (r"\bclassical cost\b",)),
    ("Quantum Cost", (r"\bquantum cost\b",)),
]


ATTACK_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Lattice Reduction Attack", (r"\blattice reduction attack\b", r"\blattice reduction attacks\b")),
    ("Primal Attack", (r"\bprimal attack\b",)),
    ("Dual Attack", (r"\bdual attack\b",)),
    ("Hybrid Attack", (r"\bhybrid attack\b", r"\bhybrid attacks\b")),
    ("Dual Hybrid Attack", (r"\bdual hybrid attack\b",)),
    ("Primal Hybrid Attack", (r"\bprimal hybrid attack\b",)),
    ("Meet-in-the-Middle", (r"\bmeet[- ]in[- ]the[- ]middle\b", r"\bmitm\b")),
    ("Guessing Attack", (r"\bguessing attack\b", r"\bguessing strategy\b")),
    ("Guess-and-Verify", (r"\bguess[- ]and[- ]verify\b",)),
    ("Drop-and-Solve", (r"\bdrop[- ]and[- ]solve\b",)),
    ("Distinguisher", (r"\bdistinguisher\b", r"\bdistinguishing\b")),
    ("Secret Recovery", (r"\bsecret recovery\b",)),
    ("Support Recovery", (r"\bsupport recovery\b",)),
    ("Sparse Secret Recovery", (r"\bsparse secret recovery\b",)),
    ("BKW", (r"\bbkw\b",)),
    ("Coded-BKW", (r"\bcoded[- ]bkw\b",)),
    ("Arora-Ge", (r"\barora[- ]ge\b",)),
    ("Linearization Attack", (r"\blinearization attack\b",)),
    ("Algebraic Attack", (r"\balgebraic attack\b",)),
    ("Decryption Failure Attack", (r"\bdecryption failure attack\b",)),
    ("Reaction Attack", (r"\breaction attack\b",)),
    ("Failure Oracle", (r"\bfailure oracle\b",)),
    ("Key Mismatch Attack", (r"\bkey mismatch attack\b",)),
    ("Side-Channel Assisted Attack", (r"\bside[- ]channel assisted\b",)),
    ("Fault Attack", (r"\bfault attack\b", r"\bfault injection\b")),
    ("Chosen Ciphertext Attack", (r"\bchosen ciphertext\b", r"\bcca\b")),
    ("Chosen Plaintext Attack", (r"\bchosen plaintext\b", r"\bcpa\b")),
    ("Multi-target Attack", (r"\bmulti[- ]target attack\b",)),
    ("Subfield Attack", (r"\bsubfield attack\b",)),
    ("Ring Attack", (r"\bring attack\b",)),
    ("Module Attack", (r"\bmodule attack\b",)),
    ("Projection Attack", (r"\bprojection attack\b",)),
    ("Covariance Attack", (r"\bcovariance attack\b",)),
    ("Score Distribution", (r"\bscore distribution\b",)),
    ("Noise Flooding Analysis", (r"\bnoise flooding\b",)),
    ("Error Amplification", (r"\berror amplification\b",)),
    ("Modulus Switching Attack", (r"\bmodulus switching attack\b",)),
    ("Secret-Error Switching", (r"\bsecret[- ]error switching\b",)),
    ("Sample Amplification", (r"\bsample amplification\b",)),
    ("Sample Selection", (r"\bsample selection\b",)),
]


PQC_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("NIST PQC", (r"\bnist pqc\b",)),
    ("Post-Quantum Cryptography", (r"\bpost[- ]quantum cryptography\b",)),
    ("PQC", (r"\bpqc\b", r"\bpost[- ]quantum\b")),
    ("CRYSTALS-Kyber", (r"\bcrystals[- ]kyber\b",)),
    ("Kyber", (r"\bkyber\b",)),
    ("ML-KEM", (r"\bml[- ]kem\b", r"\bmodule[- ]lattice[- ]based key[- ]encapsulation\b")),
    ("CRYSTALS-Dilithium", (r"\bcrystals[- ]dilithium\b",)),
    ("Dilithium", (r"\bdilithium\b",)),
    ("ML-DSA", (r"\bml[- ]dsa\b", r"\bmodule[- ]lattice[- ]based digital signature\b")),
    ("Falcon", (r"\bfalcon\b(?![- ]x\b)",)),
    ("FN-DSA", (r"\bfn[- ]dsa\b",)),
    ("NTRUEncrypt", (r"\bntruencrypt\b",)),
    ("NTRU-HRSS", (r"\bntru[- ]hrss\b",)),
    ("NTRU-HPS", (r"\bntru[- ]hps\b",)),
    ("Saber", (r"\bsaber\b",)),
    ("FrodoKEM", (r"\bfrodokem\b",)),
    ("NewHope", (r"\bnewhope\b",)),
    ("SPHINCS+", (r"\bsphincs\+\b",)),
    ("SLH-DSA", (r"\bslh[- ]dsa\b",)),
    ("Classic McEliece", (r"\bclassic mceliece\b",)),
    ("BIKE", (r"\bbike\b",)),
    ("HQC", (r"\bhqc\b",)),
    ("KEM", (r"\bkem\b", r"\bkey encapsulation\b")),
    ("PKE", (r"\bpke\b", r"\bpublic key encryption\b")),
    ("Signature", (r"\bsignature\b", r"\bsignatures\b")),
    ("Fiat-Shamir with Aborts", (r"\bfiat[- ]shamir with aborts\b",)),
    ("Fiat-Shamir", (r"\bfiat[- ]shamir\b",)),
    ("Rejection Sampling", (r"\brejection sampling\b",)),
    ("FO Transform", (r"\bfo transform\b", r"\bfujisaki[- ]okamoto\b")),
    ("CCA Security", (r"\bcca security\b", r"\bind[- ]cca\b")),
    ("CPA Security", (r"\bcpa security\b", r"\bind[- ]cpa\b")),
    ("IND-CPA", (r"\bind[- ]cpa\b",)),
    ("IND-CCA", (r"\bind[- ]cca\b",)),
    ("EUF-CMA", (r"\beuf[- ]cma\b",)),
    ("SUF-CMA", (r"\bsuf[- ]cma\b",)),
    ("QROM", (r"\bqrom\b",)),
    ("ROM", (r"\brom\b", r"\brandom oracle model\b")),
    ("Module-Lattice KEM", (r"\bmodule[- ]lattice kem\b",)),
    ("Module-Lattice Signature", (r"\bmodule[- ]lattice signature\b",)),
]


PRIMITIVE_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Module-SIS Commitment", (r"\bmodule[- ]sis commitment\b",)),
    ("SIS Commitment", (r"\bsis commitment\b",)),
    ("Lattice Commitment", (r"\blattice commitment\b",)),
    ("Commitment", (r"\bcommitment\b", r"\bcommitments\b")),
    ("Module-SIS Chameleon Hash", (r"\bmodule[- ]sis chameleon hash\b",)),
    ("Lattice Chameleon Hash", (r"\blattice chameleon hash\b",)),
    ("Chameleon Hash", (r"\bchameleon hash\b",)),
    ("Trapdoor Hash", (r"\btrapdoor hash\b",)),
    ("Hash-and-Sign", (r"\bhash[- ]and[- ]sign\b",)),
    ("Trapdoor Function", (r"\btrapdoor function\b",)),
    ("Preimage Sampling", (r"\bpreimage sampling\b",)),
    ("GPV", (r"\bgpv\b",)),
    ("Bonsai Tree", (r"\bbonsai tree\b",)),
    ("Lattice Trapdoor", (r"\blattice trapdoor\b", r"\blattice trapdoors\b")),
    ("Identity-Based Encryption", (r"\bidentity[- ]based encryption\b", r"\bibe\b")),
    ("Attribute-Based Encryption", (r"\battribute[- ]based encryption\b", r"\babe\b")),
    ("Functional Encryption", (r"\bfunctional encryption\b",)),
    ("FHE", (r"\bfhe\b", r"\bfully homomorphic encryption\b")),
    ("Homomorphic Encryption", (r"\bhomomorphic encryption\b",)),
    ("BFV", (r"\bbfv\b",)),
    ("BGV", (r"\bbgv\b",)),
    ("CKKS", (r"\bckks\b",)),
    ("TFHE", (r"\btfhe\b",)),
    ("Bootstrapping", (r"\bbootstrapping\b",)),
    ("Key Switching", (r"\bkey switching\b",)),
    ("Relinearization", (r"\brelinearization\b",)),
    ("GSW", (r"\bgsw\b",)),
    ("Lattice-Based ZK", (r"\blattice[- ]based zk\b", r"\blattice zero[- ]knowledge\b")),
    ("Zero-Knowledge", (r"\bzero[- ]knowledge\b", r"\bzk\b")),
    ("ZK-Friendly", (r"\bzk[- ]friendly\b",)),
    ("Anonymous Credential", (r"\banonymous credential\b",)),
    ("Group Signature", (r"\bgroup signature\b",)),
    ("Linkable Ring Signature", (r"\blinkable ring signature\b",)),
    ("Ring Signature", (r"\bring signature\b",)),
    ("Blind Signature", (r"\bblind signature\b",)),
    ("Redactable Signature", (r"\bredactable signature\b",)),
    ("Aggregate Signature", (r"\baggregate signature\b",)),
    ("Verifiable Encryption", (r"\bverifiable encryption\b",)),
    ("Accumulator", (r"\baccumulator\b",)),
    ("Oblivious Transfer", (r"\boblivious transfer\b", r"\bot\b")),
    ("MPC", (r"\bmultiparty computation\b", r"\bmpc\b")),
    ("Threshold Cryptography", (r"\bthreshold cryptography\b",)),
    ("Threshold Signature", (r"\bthreshold signature\b",)),
    ("Distributed Key Generation", (r"\bdistributed key generation\b", r"\bdkg\b")),
]


IMPLEMENTATION_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Side-Channel", (r"\bside[- ]channel\b", r"\bsca\b")),
    ("Fault Attack", (r"\bfault attack\b",)),
    ("Constant-Time Verification", (r"\bconstant[- ]time verification\b",)),
    ("Constant-Time", (r"\bconstant[- ]time\b",)),
    ("Timing Attack", (r"\btiming attack\b",)),
    ("Cache Attack", (r"\bcache attack\b",)),
    ("Simple Power Analysis", (r"\bsimple power analysis\b", r"\bspa\b")),
    ("Differential Power Analysis", (r"\bdifferential power analysis\b", r"\bdpa\b")),
    ("Power Analysis", (r"\bpower analysis\b",)),
    ("EM Side Channel", (r"\belectromagnetic\b", r"\bem side[- ]channel\b")),
    ("Masking", (r"\bmasking\b",)),
    ("Shuffling", (r"\bshuffling\b",)),
    ("Hiding", (r"\bhiding\b",)),
    ("Fault Injection", (r"\bfault injection\b",)),
    ("Laser Fault", (r"\blaser fault\b",)),
    ("Voltage Glitch", (r"\bvoltage glitch\b",)),
    ("Rowhammer", (r"\browhammer\b",)),
    ("Microarchitectural Leakage", (r"\bmicroarchitectural\b",)),
    ("Speculative Execution", (r"\bspeculative execution\b",)),
    ("Rejection Sampling Leakage", (r"\brejection sampling leakage\b",)),
    ("Gaussian Sampling Leakage", (r"\bgaussian sampling leakage\b",)),
    ("NTT", (r"\bntt\b", r"\bnumber theoretic transform\b")),
    ("Polynomial Multiplication", (r"\bpolynomial multiplication\b",)),
    ("Montgomery Reduction", (r"\bmontgomery reduction\b",)),
    ("Barrett Reduction", (r"\bbarrett reduction\b",)),
    ("Modular Arithmetic", (r"\bmodular arithmetic\b",)),
    ("Vectorization", (r"\bvectorization\b",)),
    ("AVX2", (r"\bavx2\b",)),
    ("NEON", (r"\bneon\b",)),
    ("ARM Cortex-M", (r"\bcortex[- ]m\b", r"\barm cortex[- ]m\b")),
    ("Embedded PQC", (r"\bembedded pqc\b", r"\bembedded\b")),
    ("Test Vectors", (r"\btest vectors\b",)),
    ("KAT", (r"\bkat\b", r"\bknown answer test\b")),
    ("Production Audit", (r"\bproduction audit\b",)),
    ("Implementation Audit", (r"\bimplementation audit\b", r"\baudit\b")),
    ("TLS", (r"\btls\b",)),
    ("Hybrid Key Exchange", (r"\bhybrid key exchange\b",)),
    ("OpenSSL", (r"\bopenssl\b",)),
    ("liboqs", (r"\bliboqs\b",)),
    ("PQClean", (r"\bpqclean\b",)),
    ("Rust", (r"\brust\b",)),
    ("C++", (r"\bc\+\+\b",)),
    ("C", (r"\bc implementation\b", r"\bin c\b")),
    ("SageMath", (r"\bsagemath\b", r"\bsage\b")),
    ("Python Prototype", (r"\bpython prototype\b", r"\bpython\b")),
    ("Reproducibility", (r"\breproducibility\b", r"\breproducible\b")),
    ("Benchmark", (r"\bbenchmark\b", r"\bbenchmarks\b")),
    ("Artifact Evaluation", (r"\bartifact evaluation\b",)),
]


AI_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("AI-assisted Lattice Cryptanalysis", (r"\bai[- ]assisted lattice cryptanalysis\b",)),
    ("Machine Learning for LWE", (r"\bmachine learning (for|on) lwe\b", r"\bml (for|on) lwe\b")),
    ("Transformer LWE", (r"\btransformer lwe\b",)),
    ("SALSA", (r"\bsalsa\b",)),
    ("TAPAS", (r"\btapas\b",)),
    ("Neural Lattice Reduction", (r"\bneural lattice reduction\b",)),
    ("Learning-Augmented Lattice Reduction", (r"\blearning[- ]augmented lattice reduction\b", r"\blalr\b")),
    ("Swin-guided Coordinate Selection", (r"\bswin[- ]guided coordinate selection\b",)),
    ("Swin Transformer", (r"\bswin transformer\b",)),
    ("Shifted Window Attention", (r"\bshifted window attention\b",)),
    ("Negative-Cyclic Modeling", (r"\bnegative[- ]cyclic\b", r"\bnegacyclic\b")),
    ("Negacyclic Shift", (r"\bnegacyclic shift\b",)),
    ("RLWE Structure Learning", (r"\brlwe structure learning\b",)),
    ("MLWE Structure Learning", (r"\bmlwe structure learning\b",)),
    ("Block-Circulant Attention", (r"\bblock[- ]circulant attention\b",)),
    ("Coordinate Selection", (r"\bcoordinate selection\b",)),
    ("Sample Selection", (r"\bsample selection\b",)),
    ("Candidate Ranking", (r"\bcandidate ranking\b",)),
    ("Hybrid Ranking", (r"\bhybrid ranking\b",)),
    ("Attack-Cost Proxy", (r"\battack[- ]cost proxy\b",)),
    ("Learned Distinguisher", (r"\blearned distinguisher\b",)),
    ("Learned Pruning", (r"\blearned pruning\b",)),
    ("BKZ Parameter Prediction", (r"\bbkz parameter prediction\b",)),
    ("Block Size Prediction", (r"\bblock size prediction\b",)),
    ("Support Prediction", (r"\bsupport prediction\b",)),
    ("Secret Support Recovery", (r"\bsecret support recovery\b",)),
    ("Sparse Secret Classification", (r"\bsparse secret classification\b",)),
    ("Graph Neural Network", (r"\bgraph neural network\b", r"\bgnn\b")),
    ("Mamba", (r"\bmamba\b",)),
    ("VMamba", (r"\bvmamba\b",)),
    ("State Space Model", (r"\bstate space model\b",)),
    ("CNN", (r"\bcnn\b",)),
    ("MLP", (r"\bmlp\b",)),
    ("Contrastive Learning", (r"\bcontrastive learning\b",)),
    ("Self-Supervised Learning", (r"\bself[- ]supervised learning\b",)),
    ("Reinforcement Learning", (r"\breinforcement learning\b", r"\brl\b")),
    ("Bayesian Optimization", (r"\bbayesian optimization\b",)),
    ("Evolutionary Search", (r"\bevolutionary search\b",)),
    ("Genetic Algorithm", (r"\bgenetic algorithm\b",)),
    ("Learning to Rank", (r"\blearning to rank\b", r"\blearning[- ]to[- ]rank\b")),
    ("Curriculum Learning", (r"\bcurriculum learning\b",)),
    ("Data Repetition", (r"\bdata repetition\b",)),
    ("Stepwise Regression", (r"\bstepwise regression\b",)),
    ("Toy Phenomenon", (r"\btoy phenomenon\b", r"\btoy\b")),
    ("Out-of-Distribution", (r"\bout[- ]of[- ]distribution\b", r"\bood\b")),
    ("Generalization", (r"\bgeneralization\b",)),
    ("Interpretability", (r"\binterpretability\b",)),
    ("Attention Analysis", (r"\battention analysis\b",)),
    ("Feature Attribution", (r"\bfeature attribution\b",)),
]


WORKFLOW_BY_PRIORITY = {
    "必须精读": "Must Read",
    "建议精读": "Recommended Read",
    "可略读": "Skim",
    "暂存": "Archive",
    "低相关": "Archive",
}


CONTEXT_LATTICE = (
    r"\blattice\b",
    r"\blwe\b",
    r"\brlwe\b",
    r"\bmlwe\b",
    r"\bsis\b",
    r"\bbkz\b",
    r"\bg6k\b",
    r"\bfplll\b",
    r"\bcryptanalysis\b",
    r"\bmodule[- ]sis\b",
    r"\bmodule[- ]lwe\b",
)

AI_CONTEXT = (
    r"\btransformer\b",
    r"\bswin\b",
    r"\bcoordinate selection\b",
    r"\bnegative[- ]cyclic\b",
    r"\bnegacyclic\b",
    r"\bmachine learning\b",
    r"\bneural\b",
    r"\bgnn\b",
    r"\bmamba\b",
    r"\bcnn\b",
    r"\bmlp\b",
    r"\breinforcement learning\b",
    r"\bbayesian optimization\b",
)


def classify_text(
    *,
    title: str = "",
    abstract: str = "",
    existing_tags: Iterable[str] = (),
    priority_label: str = "",
    suggested_action: str = "",
    reason_for_priority: str = "",
) -> TaxonomyResult:
    combined_raw = " ".join([title, abstract, reason_for_priority, " ".join(existing_tags)])
    text = normalize_text(combined_raw)

    lattice_tags: list[str] = []
    pqc_tags: list[str] = []
    attack_tags: list[str] = []
    primitive_tags: list[str] = []
    implementation_tags: list[str] = []
    ai_tags: list[str] = []
    research_tags: list[str] = []

    for tag, patterns in LATTICE_RULES:
        if _contains(text, patterns):
            _add(lattice_tags, tag)
    for tag, patterns in REDUCTION_RULES:
        if _contains(text, patterns):
            _add(lattice_tags, tag)
            _add(research_tags, "Lattice Reduction")
    for tag, patterns in PQC_RULES:
        if _contains(text, patterns):
            _add(pqc_tags, tag)
    for tag, patterns in PRIMITIVE_RULES:
        if _contains(text, patterns):
            _add(primitive_tags, tag)
    for tag, patterns in IMPLEMENTATION_RULES:
        if _contains(text, patterns):
            _add(implementation_tags, tag)

    has_lattice_context = _contains(text, CONTEXT_LATTICE)
    for tag, patterns in ATTACK_RULES:
        if _contains(text, patterns) and has_lattice_context:
            _add(attack_tags, tag)

    has_ai_context = _contains(text, AI_CONTEXT)
    if has_ai_context and has_lattice_context:
        _add(ai_tags, "AI4Lattice")
        _add(research_tags, "AI4Lattice")
        for tag, patterns in AI_RULES:
            if _contains(text, patterns):
                _add(ai_tags, tag)

    if any(tag in lattice_tags for tag in ("LWE", "Ring-LWE", "Module-LWE", "Sparse LWE")):
        _add(research_tags, "LWE/RLWE/MLWE")
    if any(tag in lattice_tags for tag in ("SIS", "Module-SIS", "Ring-SIS")):
        _add(research_tags, "SIS/Module-SIS")
    if any(tag in pqc_tags for tag in ("ML-KEM", "Kyber", "ML-DSA", "Dilithium", "Falcon", "FN-DSA")):
        _add(research_tags, "PQC Schemes")
    if attack_tags:
        _add(research_tags, "Lattice Cryptanalysis")
    if primitive_tags:
        _add(research_tags, "Lattice Primitives")
    if implementation_tags:
        if _contains(text, (r"\bside[- ]channel\b", r"\bfault\b", r"\bconstant[- ]time\b", r"\bleakage\b", r"\baudit\b")):
            _add(research_tags, "Implementation Security")
        else:
            _add(research_tags, "Implementation / Benchmark")
    if any(tag in primitive_tags for tag in ("FHE", "BFV", "BGV", "CKKS", "TFHE", "Bootstrapping")):
        _add(research_tags, "FHE")
    if any(tag in primitive_tags for tag in ("Zero-Knowledge", "ZK-Friendly", "Anonymous Credential")):
        _add(research_tags, "ZK-friendly PQ Privacy")

    workflow = WORKFLOW_BY_PRIORITY.get(priority_label)
    if workflow:
        _add(research_tags, workflow)
    if "idea" in suggested_action.lower() or "paper" in suggested_action.lower():
        _add(research_tags, "Paper Idea")
    if _contains(text, (r"\bexperiment\b", r"\bbenchmark\b")):
        _add(research_tags, "Experiment Candidate")
    if _contains(text, (r"\btoy\b", r"\bsmall parameter", r"\bsmall[- ]parameter", r"\bsynthetic\b")):
        _add(research_tags, "Toy Benchmark")
    if _contains(text, (r"\bproof\b", r"\bsecurity analysis\b")):
        _add(research_tags, "Security Proof Needed")
    if _contains(text, (r"\bparameter estimation\b", r"\bestimator\b")):
        _add(research_tags, "Parameter Estimation Needed")
    if _contains(text, (r"\btodo_verify\b", r"\btodo verify\b")):
        _add(research_tags, "TODO_VERIFY")

    zotero_tags = build_zotero_tags(research_tags, lattice_tags, pqc_tags, attack_tags, primitive_tags, implementation_tags, ai_tags)
    obsidian_links = build_obsidian_links(lattice_tags, pqc_tags, attack_tags, primitive_tags, implementation_tags, ai_tags, research_tags)
    return TaxonomyResult(
        research_tags=_stable(research_tags),
        lattice_tags=_stable(lattice_tags),
        pqc_tags=_stable(pqc_tags),
        attack_tags=_stable(attack_tags),
        primitive_tags=_stable(primitive_tags),
        implementation_tags=_stable(implementation_tags),
        ai_tags=_stable(ai_tags),
        zotero_tags=zotero_tags,
        obsidian_links=obsidian_links,
    )


def build_zotero_tags(*tag_groups: Iterable[str]) -> list[str]:
    tags: list[str] = []
    for group in tag_groups:
        for tag in group:
            flat = re.sub(r"[^a-z0-9+]+", "-", tag.lower()).strip("-")
            if flat:
                _add(tags, flat)
    return _stable(tags)


OBSIDIAN_CONCEPTS = {
    "Lattice": "[[Lattice Cryptography]]",
    "LWE": "[[LWE]]",
    "Ring-LWE": "[[RLWE]]",
    "Module-LWE": "[[MLWE]]",
    "Sparse LWE": "[[Sparse LWE]]",
    "SIS": "[[SIS]]",
    "Module-SIS": "[[Module-SIS]]",
    "Ring-SIS": "[[Ring-SIS]]",
    "NTRU": "[[NTRU]]",
    "BKZ": "[[BKZ]]",
    "LLL": "[[LLL]]",
    "G6K": "[[G6K]]",
    "fplll": "[[fplll]]",
    "Primal Attack": "[[Primal Attack]]",
    "Dual Attack": "[[Dual Attack]]",
    "Hybrid Attack": "[[Hybrid Attack]]",
    "Secret Recovery": "[[Secret Recovery]]",
    "ML-KEM": "[[ML-KEM]]",
    "Kyber": "[[Kyber]]",
    "ML-DSA": "[[ML-DSA]]",
    "Dilithium": "[[Dilithium]]",
    "Falcon": "[[Falcon]]",
    "Commitment": "[[Commitment]]",
    "Module-SIS Commitment": "[[Module-SIS Commitment]]",
    "Chameleon Hash": "[[Chameleon Hash]]",
    "Module-SIS Chameleon Hash": "[[Module-SIS Chameleon Hash]]",
    "FHE": "[[FHE]]",
    "CKKS": "[[CKKS]]",
    "BFV": "[[BFV]]",
    "BGV": "[[BGV]]",
    "TFHE": "[[TFHE]]",
    "Zero-Knowledge": "[[Zero-Knowledge]]",
    "ZK-Friendly": "[[ZK-friendly PQ Privacy]]",
    "AI4Lattice": "[[AI4Lattice]]",
    "Transformer LWE": "[[Transformer LWE]]",
    "Swin Transformer": "[[Swin Transformer for LWE]]",
    "Swin-guided Coordinate Selection": "[[Swin-guided Coordinate Selection]]",
    "Lattice Reduction": "[[Lattice Reduction]]",
    "Lattice Cryptanalysis": "[[Lattice Cryptanalysis]]",
    "Implementation Security": "[[PQC Implementation Security]]",
}


def build_obsidian_links(*tag_groups: Iterable[str]) -> list[str]:
    links: list[str] = []
    for group in tag_groups:
        for tag in group:
            link = OBSIDIAN_CONCEPTS.get(tag)
            if link:
                _add(links, link)
    return _stable(links)
