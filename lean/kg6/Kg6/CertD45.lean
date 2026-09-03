/-
The D=4 and D=5 computational certificates (stdlib-only, native_decide).

D=4: 2,160 ordered quadruples of nonempty pairwise edge-disjoint PM
     subsets -> 5 S_6 orbits -> 4,917 rows -> 0 survivors of (b)/(c).
D=5: 720 = 6 * 5! ordered quintuples (each an ordered 1-factorization)
     -> 1 orbit -> 1 row -> 0 survivors.

Data (the reps) is generated from the independently audited Python
artifacts (d4_reps.pkl, d5_reps.pkl).
-/
import Kg6.Cert
import Lean

namespace Kg6

abbrev Classes := List (List Nat)

/-- Zip a list with its indices. -/
def zipIdxOf {α : Type} (xs : List α) : List (Nat × α) :=
  let rec go : List α → Nat → List (Nat × α)
    | [], _ => []
    | x :: xs, i => (i, x) :: go xs (i + 1)
  go xs 0

/-- First element of the list for which f returns `some`. -/
def findSomeIn {α β : Type} (xs : List α) (f : α → Option β) : Option β :=
  xs.foldl (fun acc x => match acc with | some _ => acc | none => f x) none

/-- Relabel one PM class under a vertex permutation (image list). -/
def relabelClass (p : List Nat) (P : List Nat) : List Nat :=
  isort (P.map (relabelPM p))

/-- Relabel a list of classes. -/
def relabelClasses (p : List Nat) (cs : Classes) : Classes :=
  cs.map (relabelClass p)

/-- Strict lexicographic order on lists of lists. -/
def listListLt : List (List Nat) → List (List Nat) → Bool
  | [], _ :: _ => true
  | _ :: _, [] => false
  | a :: as, b :: bs => listLt a b || (a == b && listListLt as bs)
  | [], [] => false

/-- Canonical form of a class list: lexicographic min over the 720 perms. -/
@[noinline]
def canonKeyD (cs : Classes) : Classes :=
  perms6Lit.foldl (fun best p => let k := relabelClasses p cs; if listListLt k best then k else best) cs

/-- Pairwise edge-disjointness of the classes. -/
def classesDisjoint (classes : Classes) : Bool :=
  (zipIdxOf classes).all fun (i, A) =>
    (zipIdxOf classes).all fun (j, B) => i == j || edgeDisjoint A B

/-- All ordered D-tuples of nonempty pairwise edge-disjoint PM subsets. -/
def classEnumD (D : Nat) : List Classes :=
  let rec go : Nat → List Nat → List Classes → List Classes
    | 0, _, acc => acc
    | k + 1, avail, acc =>
      (subsetsOf avail).flatMap fun P =>
        if P.isEmpty then []
        else
          let avail2 := avail.filter (fun m => edgeDisjoint P [m])
          go k avail2 (acc.map (fun cs => cs ++ [P]))
  let base := go D (List.range 15) [[]]
  base.filter fun cs => cs.length == D && classesDisjoint cs

/-- The 5 D=4 orbit representatives (PM indices), from d4_reps.pkl. -/
def repsD4 : List Classes :=
  [ [[0], [4], [8], [10]],
    [[0], [4], [8], [10, 12]],
    [[0], [4], [8, 10], [12]],
    [[0], [5, 7], [9], [13]],
    [[1, 3], [7], [11], [12]] ]

/-- The D=5 orbit representative (the ordered 1-factorization). -/
def repsD5 : List Classes :=
  [ [[0], [4], [8], [10], [12]] ]

/-- Forced color of edge e under a class list (classes carry colors 0..D-1
    by position); none if free. -/
def edgeColorOfD (classes : Classes) (e : Nat) : Option Nat :=
  findSomeIn (zipIdxOf classes) fun (i, P) =>
    if (P.flatMap (fun m => getOr pms m [])).contains e then some i else none

/-- Free edges of a class list. -/
def freeEdgesD (classes : Classes) : List Nat :=
  (List.range 15).filter (fun e => edgeColorOfD classes e = none)

/-- Full 15-entry row for D colors: forced edges get (i,i) = option D*i+i;
    free edges get the digits in free-edge order. -/
def fullRowOfD (D : Nat) (classes : Classes) (digits : List Nat) : List Nat :=
  (List.range 15).map fun e =>
    match edgeColorOfD classes e with
    | some i => D * i + i
    | none =>
      match indexOfNat (freeEdgesD classes) e with
      | some j => getOr digits j (D * D)
      | none => D * D

/-- All rows of a class list for D colors (all (D^2+1)^F assignments). -/
def rowsOfD (D : Nat) (classes : Classes) : List (List Nat) :=
  let F := (freeEdgesD classes).length
  let base := D * D + 1
  (List.range (base ^ F)).map fun n => fullRowOfD D classes (unrankDigits F base n)

/-- Generic structural check for D colors: class-membership (b) + L3 (c). -/
def structOkD (D : Nat) (classes : Classes) (row : Nat → Nat) : Bool :=
  let monoCodes := (List.range D).map (fun i => monoCode D i)
  let clsOf (m : Nat) : Int :=
    match findSomeIn (zipIdxOf classes) fun (i, P) =>
      if P.contains m then some i else none with
    | some i => Int.ofNat i
    | none => -1
  let condB := (List.range 15).all fun m =>
    let c := clsOf m
    if c < 0 then true
    else
      (List.range D).all fun i =>
        let ci : Int := i
        c == ci || ivcCodeRow (D := D) row (getOr pms m []) != some (monoCode D i)
  let condC := (List.range 15).all fun m =>
    match ivcCodeRow (D := D) row (getOr pms m []) with
    | none => true
    | some c =>
      if monoCodes.contains c then true
      else
        (List.range 15).any fun m2 =>
          m2 != m && ivcCodeRow (D := D) row (getOr pms m2 []) == some c
  condB && condC

/-- Batch check for D colors: every row fails (b) or (c). -/
def batchOkD (D : Nat) (classes : Classes) : Bool :=
  (rowsOfD D classes).all fun row =>
    !(structOkD D classes (fun e => getOr row e (D * D)))

/-- D4: raw class count. -/
theorem d4_class_count : (classEnumD 4).length = 2160 := by
  native_decide

/-- D4: orbit completeness (canonical keys of all raw classes are rep keys). -/
theorem d4_orbit_cover :
    (classEnumD 4).all fun cs =>
      (repsD4.map canonKeyD).contains (canonKeyD cs) := by
  native_decide

/-- D4: batch elimination. -/
theorem d4_batch_ok : repsD4.all (batchOkD 4) := by
  native_decide

/-- D5: raw class count (= 6 * 5! = 720). -/
theorem d5_class_count : (classEnumD 5).length = 720 := by
  native_decide

/-- D5: orbit completeness. -/
theorem d5_orbit_cover :
    (classEnumD 5).all fun cs =>
      (repsD5.map canonKeyD).contains (canonKeyD cs) := by
  native_decide

/-- D5: batch elimination (the single 1-factorization row). -/
theorem d5_batch_ok : repsD5.all (batchOkD 5) := by
  native_decide

end Kg6
