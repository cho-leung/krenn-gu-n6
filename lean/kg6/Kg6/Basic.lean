/-
Data layer for the (6,D) monochromatic-graph certificate (stdlib-only).
Vertices 0..5; the 15 edges of K_6; the 15 perfect matchings; IVC codes;
the structural conditions (b) no-new-mono and (c) L3.

All data literals are generated from the independently audited Python
implementation (audit/verification_2026-09-03/).
-/
import Lean

namespace Kg6

/-- The 15 edges of K_6, listed as pairs (u, v) with u < v. -/
def edges : List (Nat × Nat) :=
  [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 2), (1, 3), (1, 4), (1, 5),
   (2, 3), (2, 4), (2, 5), (3, 4), (3, 5), (4, 5)]

/-- The 15 perfect matchings of K_6, as lists of edge indices. -/
def pms : List (List Nat) :=
  [[0, 9, 14], [0, 10, 13], [0, 11, 12], [1, 6, 14], [1, 7, 13], [1, 8, 12],
   [2, 5, 14], [2, 7, 11], [2, 8, 10], [3, 5, 13], [3, 6, 11], [3, 8, 9],
   [4, 5, 12], [4, 6, 10], [4, 7, 9]]

/-- Safe list lookup with a default (stdlib-only). -/
def getOr {α : Type} (xs : List α) (i : Nat) (d : α) : α :=
  match xs.drop i with
  | [] => d
  | y :: _ => y

/-- Count occurrences of v in xs. -/
def countOf (xs : List Nat) (v : Nat) : Nat :=
  xs.foldl (fun acc x => if x == v then acc + 1 else acc) 0

/-- A 3-edge set covers all six vertices iff each of 0..5 occurs exactly once. -/
def coversVertices (M : List Nat) : Bool :=
  let vs := M.flatMap fun e =>
    let uv := getOr edges e (0, 0)
    [uv.1, uv.2]
  (List.range 6).all fun v => countOf vs v == 1

/-- Brute-force enumeration of all 3-edge subsets of K_6 that cover all vertices. -/
def pmsBrute : List (List Nat) :=
  ((List.range 15).flatMap fun a =>
    (List.range 15).flatMap fun b =>
      (List.range 15).map fun c => [a, b, c])
  |>.filter (fun t =>
    (getOr t 0 99 < getOr t 1 99) && (getOr t 1 99 < getOr t 2 99) && coversVertices t)

theorem pms_eq_brute : pms = pmsBrute := by
  native_decide

/-- Powers of D: D^0 .. D^5. -/
def powers (D : Nat) : List Nat :=
  [1, D, D * D, D * D * D, D * D * D * D, D * D * D * D * D]

/-- A coloring of the 15 edges: option index o, where o < D^2 means color
    pair (o / D, o % D) and o = D^2 means ABSENT. -/
abbrev Coloring (D : Nat) := Fin 15 → Fin (D * D + 1)

/-- Look up a coloring by Nat edge index (out of range = absent). -/
def colAt {D : Nat} (col : Coloring D) (e : Nat) : Nat :=
  if h : e < 15 then (col ⟨e, h⟩).val else D * D

/-- IVC base-D code of perfect matching M (edge indices) under col;
    `none` if M uses an absent edge. -/
def ivcCode {D : Nat} (col : Coloring D) (M : List Nat) : Option Nat :=
  let pow := powers D
  M.foldl (fun acc e =>
    match acc with
    | none => none
    | some code =>
      let o := colAt col e
      if o ≥ D * D then none
      else
        let a := o / D
        let b := o % D
        let (u, v) := getOr edges e (0, 0)
        some (code + a * getOr pow u 1 + b * getOr pow v 1))
    (some 0)

/-- Monochromatic code of color i (i^6 in base D). -/
def monoCode (D i : Nat) : Nat :=
  i * ((powers D).foldl (fun acc p => acc + p) 0)

/-- IVC code of PM m from a ROW (option index per edge, 0..8 = color pair,
    9 = absent), read as a function from edge indices. -/
def ivcCodeRow {D : Nat} (row : Nat → Nat) (M : List Nat) : Option Nat :=
  let pow := powers D
  M.foldl (fun acc e =>
    match acc with
    | none => none
    | some code =>
      let o := row e
      if o ≥ D * D then none
      else
        let a := o / D
        let b := o % D
        let (u, v) := getOr edges e (0, 0)
        some (code + a * getOr pow u 1 + b * getOr pow v 1))
    (some 0)

/-- Class of PM m from a row: 0/1/2 for the three mono classes, -1 mixed,
    -2 dead. -/
def pmClassOfRow3 (row : Nat → Nat) (m : Nat) : Int :=
  match ivcCodeRow (D := 3) row (getOr pms m []) with
  | none => -2
  | some c =>
    if c == monoCode 3 0 then 0
    else if c == monoCode 3 1 then 1
    else if c == monoCode 3 2 then 2
    else -1

/-- Condition (b) relative to a class triple: no PM outside class i
    realizes the mono-i IVC. -/
def condB3 (T : (List Nat × List Nat × List Nat)) (row : Nat → Nat) : Bool :=
  let P0 := T.1
  let P1 := T.2.1
  let P2 := T.2.2
  let clsOf (m : Nat) : Int :=
    if P0.contains m then 0 else if P1.contains m then 1 else if P2.contains m then 2 else -1
  (List.range 15).all fun m =>
    let c := clsOf m
    if c < 0 then true
    else
      (List.range 3).all fun i =>
        let ci : Int := i
        c == ci || ivcCodeRow (D := 3) row (getOr pms m []) != some (monoCode 3 i)

/-- Condition (c): L3 — every realized non-mono IVC code appears at least twice. -/
def condC3 (T : (List Nat × List Nat × List Nat)) (row : Nat → Nat) : Bool :=
  (List.range 15).all fun m =>
    match ivcCodeRow (D := 3) row (getOr pms m []) with
    | none => true
    | some c =>
      if c == monoCode 3 0 || c == monoCode 3 1 || c == monoCode 3 2 then true
      else
        (List.range 15).any fun m2 =>
          m2 != m && ivcCodeRow (D := 3) row (getOr pms m2 []) == some c

/-- The structural filter: (b) and (c). -/
def structOk3 (T : (List Nat × List Nat × List Nat)) (row : Nat → Nat) : Bool :=
  condB3 T row && condC3 T row

end Kg6
