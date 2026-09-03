/-
The D=3 computational certificates (stdlib-only, native_decide):

  C1: triple enumeration count  == 5,610
  C2: the 24 orbit representatives cover every class (canonical keys)
  C3: the complete batch over all 2,033,610 assignments eliminates every
      row by (b) no-new-mono or (c) L3.

Data (the 24 reps) is generated from the independently audited Python
artifacts (triples_cache.pkl).
-/
import Kg6.Basic
import Lean

namespace Kg6

/-- Index of the first element satisfying p (stdlib-only helper). -/
def idxOfAux {α : Type} : List α → Nat → (α → Bool) → Option Nat
  | [], _, _ => none
  | x :: xs, i, p => if p x then some i else idxOfAux xs (i + 1) p

def indexOfP {α : Type} (xs : List α) (p : α → Bool) : Option Nat :=
  idxOfAux xs 0 p

def indexOfNat (xs : List Nat) (v : Nat) : Option Nat :=
  indexOfP xs (fun x => x == v)

def indexOfPair (xs : List (Nat × Nat)) (v : Nat × Nat) : Option Nat :=
  indexOfP xs (fun x => x == v)

/-- All subsets of a list (in list order; each subset appears once). -/
def subsetsOf {α : Type} (xs : List α) : List (List α) :=
  xs.foldr (fun x acc => acc ++ acc.map (fun s => x :: s)) [[]]

/-- Edge-disjointness: no common edge index between the PM-edge unions. -/
def edgeDisjoint (A B : List Nat) : Bool :=
  let eB := B.flatMap (fun m => getOr pms m [])
  (A.flatMap (fun m => getOr pms m [])).all (fun e => !(eB.contains e))

/-- All ordered triples (P0, P1, P2) of nonempty pairwise edge-disjoint PM subsets. -/
def tripleEnum : List (List Nat × List Nat × List Nat) :=
  (subsetsOf (List.range 15)).flatMap fun P0 =>
    if P0.isEmpty then []
    else
      let disj0 := (List.range 15).filter (fun m => edgeDisjoint P0 [m])
      (subsetsOf disj0).flatMap fun P1 =>
        if P1.isEmpty then []
        else
          let disj1 := (List.range 15).filter (fun m => edgeDisjoint P0 [m] && edgeDisjoint P1 [m])
          (subsetsOf disj1).flatMap fun P2 =>
            if P2.isEmpty then []
            else [(P0, P1, P2)]

/-- Insertion sort of a Nat list (ascending). -/
def isort (xs : List Nat) : List Nat :=
  let rec insert : List Nat → Nat → List Nat
    | [], x => [x]
    | y :: ys, x => if x ≤ y then x :: y :: ys else y :: insert ys x
  xs.foldl insert []

/-- All 720 bijective relabelings of the six vertices, as image lists. -/
def perms6 : List (List Nat) :=
  ((List.range 6).flatMap fun a =>
    (List.range 6).flatMap fun b =>
      (List.range 6).flatMap fun c =>
        (List.range 6).flatMap fun d =>
          (List.range 6).flatMap fun e =>
            (List.range 6).map fun f => [a, b, c, d, e, f]))
  |>.filter fun p =>
    (List.range 6).all fun i =>
      (List.range 6).all fun j => i == j || getOr p i 99 != getOr p j 99

/-- Edge index of a pair (u, v) with u < v. -/
def edgeIdxOf (u v : Nat) : Nat :=
  (indexOfPair edges (u, v)).getD 0

/-- Relabel PM index m under the image list p (a bijection). -/
def relabelPM (p : List Nat) (m : Nat) : Nat :=
  let es := (getOr pms m []).map fun e =>
    let (u, v) := getOr edges e (0, 0)
    let pu := getOr p u 0
    let pv := getOr p v 0
    if pu < pv then edgeIdxOf pu pv else edgeIdxOf pv pu
  let a := getOr es 0 99
  let b := getOr es 1 99
  let c := getOr es 2 99
  -- sort three indices ascending
  let ab := if a ≤ b then [a, b] else [b, a]
  let x := getOr ab 0 99
  let y := getOr ab 1 99
  let s := if c ≤ x then [c, x, y] else if c ≤ y then [x, c, y] else [x, y, c]
  (indexOfP pms (fun M => M == s)).getD 0

abbrev Triple := List Nat × List Nat × List Nat

/-- Relabel a triple under p. -/
def relabelT (p : List Nat) (T : Triple) : Triple :=
  (isort (T.1.map (relabelPM p)), isort (T.2.1.map (relabelPM p)), isort (T.2.2.map (relabelPM p)))

/-- Strict lexicographic order on Nat lists. -/
def listLt : List Nat → List Nat → Bool
  | [], _ :: _ => true
  | _ :: _, [] => false
  | x :: xs, y :: ys => x < y || (x == y && listLt xs ys)
  | [], [] => false

/-- Lexicographic order on triples of lists. -/
def keyLt (k1 k2 : Triple) : Bool :=
  listLt k1.1 k2.1 ||
    (k1.1 == k2.1 &&
      (listLt k1.2.1 k2.2.1 || (k1.2.1 == k2.2.1 && listLt k1.2.2 k2.2.2)))

/-- Canonical key of a triple: lexicographic minimum over the 720 perms. -/
def canonKey (T : Triple) : Triple :=
  perms6.foldl (fun best p => let k := relabelT p T; if keyLt k best then k else best) T

/-- The 24 orbit representatives (PM indices, sorted classes), from the
    audited Python triples_cache.pkl. -/
def reps : List Triple :=
  [([0], [4], [8]), ([0], [4], [8, 10]), ([0], [4], [8, 10, 12]), ([0], [4], [13]),
   ([0], [4], [8, 13]), ([0], [4], [8, 10, 13]), ([0], [4], [8, 10, 12, 13]),
   ([0], [4, 5], [10]), ([0], [4, 5], [10, 13]), ([0], [5, 7], [9]),
   ([0], [5, 7], [9, 13]), ([0], [4, 5, 7], [13]), ([0], [5, 7, 9], [13]),
   ([0], [4, 5, 7, 9], [13]), ([0, 1], [5], [7]), ([0, 1], [5], [7, 10]),
   ([0, 1], [7, 10], [5]), ([0, 1], [7, 10], [5, 12]), ([1, 3], [7], [11]),
   ([1, 3], [7], [11, 12]), ([1, 3], [7, 11], [12]), ([0, 1, 3], [7], [12]),
   ([2, 4, 6], [11], [13]), ([1, 3, 4, 7], [11], [12])]

def repsKeys : List Triple := reps.map canonKey

/-- Forced color of edge e under triple T: none if e is free. -/
def edgeColorOf (T : Triple) (e : Nat) : Option Nat :=
  if (T.1.flatMap (fun m => getOr pms m [])).contains e then some 0
  else if (T.2.1.flatMap (fun m => getOr pms m [])).contains e then some 1
  else if (T.2.2.flatMap (fun m => getOr pms m [])).contains e then some 2
  else none

/-- Free edges of T, in ascending order. -/
def freeEdges (T : Triple) : List Nat :=
  (List.range 15).filter (fun e => edgeColorOf T e = none)

/-- Position of e among the free edges (none if forced). -/
def freePosOf (T : Triple) (e : Nat) : Option Nat :=
  indexOfNat (freeEdges T) e

/-- Digit expansion of n in base `base`, length F (least significant first). -/
def unrankDigits (F base n : Nat) : List Nat :=
  (List.range F).map fun j => (n / (base ^ j)) % base

/-- Full 15-entry row: forced edges get (i,i) = option 3i+i; free edges get
    the digits in free-edge order. -/
def fullRowOf (T : Triple) (digits : List Nat) : List Nat :=
  (List.range 15).map fun e =>
    match edgeColorOf T e with
    | some i => 3 * i + i
    | none =>
      match freePosOf T e with
      | some j => getOr digits j 9
      | none => 9

/-- All rows of T (all 10^F free-edge assignments). -/
def rowsOf (T : Triple) : List (List Nat) :=
  let F := (freeEdges T).length
  (List.range (10 ^ F)).map fun n => fullRowOf T (unrankDigits F 10 n)

/-- The batch check for T: every row fails (b) or (c). -/
def batchOk (T : Triple) : Bool :=
  (rowsOf T).all fun row =>
    !(structOk3 T (fun e => getOr row e 9))

/-- C1: the raw class count. -/
theorem triple_count : tripleEnum.length = 5610 := by
  native_decide

/-- C2: orbit completeness — every class's canonical key is a rep key. -/
theorem orbit_cover : tripleEnum.all (fun T => repsKeys.contains (canonKey T)) := by
  native_decide

/-- C3: batch elimination — all 24 reps, all 2,033,610 rows, fail (b) or (c). -/
theorem batch_ok_all : reps.all batchOk := by
  native_decide

end Kg6
