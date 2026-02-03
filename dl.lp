#const l=2.
layer(1..l).

% ============================================
% Rules
% ============================================

rule(top;bottom;negation;conjunction;disjunction;exists;forall;copy).

% ============================================
% Dynamic selection of rules
% ============================================

% selectRule(Layer, Concept, Rule) is guessed by ASP
{ selectRule(L, C, R) : rule(R) } = 1 :- layer(L), concept(C).


% ============================================
% Parameters (dynamic, guessed)
% ============================================

% For conjunction and disjunction
{ param(L, C, D) : concept(D) } = 1 :- selectRule(L, C, conjunction).
{ param(L, C, D) : concept(D) } = 1 :- selectRule(L, C, disjunction).

% For exists and forall relations
{ param(L, C, R) : role(R)} = 1 :- selectRule(L, C, exists).
{ param(L, C, R) : role(R)} = 1 :- selectRule(L, C, forall).

% ============================================
% DL constructors
% ============================================

% Top
concept(C, S, O, L) :- selectRule(L, C, top), state(S), object(O).

% Bottom
%:- concept(C, S, O, L), selectRule(L, C, bottom), state(S), object(O).

% Negation
concept(C, S, O, L) :- selectRule(L, C, negation), state(S), object(O), 
                        not concept(C, S, O, L-1).

% Conjunction
concept(C, S, O, L) :- selectRule(L, C, conjunction), param(L, C, D),
                   concept(C, S, O, L-1), concept(D, S, O, L-1).

% Disjunction
concept(C, S, O, L) :- selectRule(L, C, disjunction), concept(C, S, O, L-1).
concept(C, S, O, L) :- selectRule(L, C, disjunction), param(L, C, D), concept(D, S, O, L-1).

% Existential restriction
concept(C, S, O1, L) :- selectRule(L, C, exists), param(L, C, R),
                        holds(S,(R,O1,O2)),  concept(C, S, O2, L-1).

% Universal restriction
concept(C, S, O1, L) :- selectRule(L, C, forall), param(L, C, R), state(S), object(O1),
                         concept(C, S, O2, L-1) : holds(S,(R,O1,O2)).

% Copy
concept(C, S, O, L) :- selectRule(L, C, copy), concept(C, S, O, L-1).

% ============================================
% Features
% ============================================

{boolean_feature(C); numerical_feature(C)} = 1 :- select_concept(C).

% boolean feature: true if any O exists s.t. concept(C,S,O,l)
value(C,S,1) :- concept(C,S,O,l), boolean_feature(C).
value(C,S,0) :- not value(C,S,1), boolean_feature(C), state(S).
evaluation(C,S,V) :- value(C,S,V), boolean_feature(C).

% numerical feature: count number of O
value(C,S,N) :- N = #count{ O : concept(C,S,O,l) }, numerical_feature(C), state(S).
evaluation(C,S,1) :- value(C,S,N), N=0, numerical_feature(C).
evaluation(C,S,0) :- value(C,S,N), N>0, numerical_feature(C).

% nullary feature
 :- select_nullary(P), holds(S,(P,)).
value(P,S,0) :- select_nullary(P), state(S), not value(P,S,1).
evaluation(P,S,V) :- value(P,S,V), select_nullary(P).

% ============================================
% Delta
% ============================================

delta(S1,S2,C,up) :- transition(S1,S2), value(C,S1,N1), value(C,S2,N2),
                        N2>N1.
delta(S1,S2,C,down) :- transition(S1,S2), value(C,S1,N1), value(C,S2,N2),
                        N1>N2.
delta(S1,S2,C,eq) :- transition(S1,S2), value(C,S1,N1), value(C,S2,N2),
                        N1=N2.

% ============================================
% Planning
% ============================================

{select_concept(C)} :- concept(C).
select(C) :- select_concept(C).
{select_nullary(P)} :- nullary(P).
select(P) :- select_nullary(P).


1{good(S1,S2) : transition(S1,S2)} :- live(S1), not goal(S1).  
%:- good(S1,S2), not live(S2).      

distinguishable(S1,S2) :- state(S1), state(S2), select(C), evaluation(C,S1,V1), evaluation(C,S2,V2), V1!=V2.
:- goal(S1), state(S2), not goal(S2), not distinguishable(S1,S2).

%D2 Separability: if (s, s′) is a “good” transition then any other transition (t, t′) where the selected features change exactly as in (s, s′) must be “good” as well.
d2(S1,S2,T1,T2) :- transition(S1,S2), transition(T1,T2), select(C), delta(S1,S2,C,DS), delta(T1,T2,C,DT), DS!=DT.
:- good(S1,S2), transition(T1,T2), not good(T1,T2), not d2(S1,S2,T1,T2).

% ============================================
% D1–D2 Relation (Determinism) [Optional] 
% ============================================

% D1–D2 constraint:
% If S1,T1 are indistinguishable, then every outgoing S1→S2 must have a matching T1→T2
%:- state(S1), state(T1), not distinguishable(S1,T1), transition(S1,S2), not matchedTransition(S1,S2,T1).

% S1→S2 matches some T1→T2
%matchedTransition(S1,S2,T1) :- transition(S1,S2), transition(T1,T2), sameDelta(S1,S2,T1,T2).

% Matching transitions require no delta differences
%sameDelta(S1,S2,T1,T2) :-
%    transition(S1,S2),
%    transition(T1,T2),
%    not diffDelta(S1,S2,T1,T2).

% A difference in delta is observed if selected(C) and both deltas exist
%diffDelta(S1,S2,T1,T2) :-
%    transition(S1,S2),
%    transition(T1,T2),
%    select(C),
%    delta(S1,S2,C,D1),
%    delta(T1,T2,C,D2),
%    D1 != D2.

% ============================================
% Value Function 
% ============================================

#const delta=2.
dist(0..D) :- max_v_star(D).
{v(S,D) : dist(D), D_star <= D, D <= delta*D_star} = 1 :- state(S), live(S), v_star(S,D_star).
:- good(S1,S2), v(S1,D1), v(S2,D2), D1 <= D2.

% Optimization 
%#minimize{1@10,C: select(C)}.
#maximize{1@5,L,C: selectRule(L, C, copy)}.
#maximize{1@3,C: boolean_feature(C)}.