#const t=3.
time(1..t).

% ============================================
% Rules
% ============================================

rule(top;bottom;negation;conjunction;disjunction;exists;forall;nominal).

% ============================================
% Dynamic selection of rules
% ============================================

% selectRule(Time, Concept, Rule) is guessed by ASP
{ selectRule(T, C, R) : rule(R) } = 1 :- time(T), concept(C).

% ============================================
% Parameters (dynamic, guessed)
% ============================================

% For conjunction and disjunction
{ param(T, C, D) : concept(D) } = 1 :- selectRule(T, C, conjunction).
{ param(T, C, D) : concept(D) } = 1 :- selectRule(T, C, disjunction).

% For exists and forall relations
{ paramR(T, C, R) : role(R)} = 1 :- selectRule(T, C, exists).
{ paramR(T, C, R) : role(R)} = 1 :- selectRule(T, C, forall).

% For nominals
{ paramN(T, C, O) : object(O)} = 1 :- selectRule(T, C, nominal).


% ============================================
% DL constructors
% ============================================

% Top
concept(C, S, O, T) :- selectRule(T, C, top), state(S), time(T), object(O).

% Bottom
%:- concept(C, S, O, T), selectRule(T, C, bottom), state(S), time(T), object(O).

% Negation
concept(C, S, O, T) :- selectRule(T, C, negation), state(S), time(T), object(O), 
                        not concept(C, S, O, T-1).

% Conjunction
concept(C, S, O, T) :- selectRule(T, C, conjunction), param(T, C, D), time(T), object(O),
                   concept(C, S, O, T-1), concept(D, S, O, T-1).

% Disjunction
concept(C, S, O, T) :- selectRule(T, C, disjunction), time(T), object(O),
                   concept(C, S, O, T-1).
concept(C, S, O, T) :- selectRule(T, C, disjunction), param(T, C, D), time(T), object(O),
                   concept(D, S, O, T-1).

% Existential restriction
concept(C, S, O1, T) :- selectRule(T, C, exists), time(T), paramR(T, C, R),
                        holds(S,(R,O1,O2)),  concept(C, S, O2, T-1).

% Universal restriction
concept(C, S, O1, T) :- selectRule(T, C, forall), paramR(T, C, R), state(S), time(T), object(O1),
                         concept(C, S, O2, T-1) : holds(S,(R,O1,O2)).

% nominals
concept(C, S, O, T) :- selectRule(T, C, nominal), paramN(T, C, O), state(S), time(T), object(O).

% ============================================
% Features
% ============================================

{boolean_feature(C); numerical_feature(C)} = 1 :- select(C).

% boolean feature: true if any O exists s.t. concept(C,S,O,t)
value(C,S,1) :- concept(C,S,O,t), boolean_feature(C).
value(C,S,0) :- not value(C,S,1), boolean_feature(C), state(S).
evaluation(C,S,V) :- value(C,S,V), boolean_feature(C).

% numerical feature: count number of O
value(C,S,N) :- N = #count { O : concept(C,S,O,t) }, numerical_feature(C), state(S).
evaluation(C,S,1) :- value(C,S,N), N=0, numerical_feature(C).
evaluation(C,S,0) :- value(C,S,N), N>0, numerical_feature(C).

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

{select(C)} :- concept(C).


1{good(S1,S2) : transition(S1,S2)} :- live(S1), not goal(S1).  
%:- good(S1,S2), not live(S2).      

distinguishable(S1,S2) :- state(S1), state(S2), select(C), evaluation(C,S1,V1), evaluation(C,S2,V2), V1!=V2.
:- goal(S1), state(S2), not goal(S2), not distinguishable(S1,S2).

%D2 Separability: if (s, s′) is a “good” transition then any other transition (t, t′) where the selected features change exactly as in (s, s′) must be “good” as well.
d2(S1,S2,T1,T2) :- transition(S1,S2), transition(T1,T2), select(C), delta(S1,S2,C,DS), delta(T1,T2,C,DT), DS!=DT.
:- good(S1,S2), transition(T1,T2), not good(T1,T2), not d2(S1,S2,T1,T2).

% ============================================
% D1–D2 Relation
% ============================================

% D1–D2 constraint:
% If S1,T1 are indistinguishable, then every outgoing S1→S2 must have a matching T1→T2
:- state(S1), state(T1), not distinguishable(S1,T1), transition(S1,S2), not matchedTransition(S1,S2,T1).

% S1→S2 matches some T1→T2
matchedTransition(S1,S2,T1) :- transition(S1,S2), transition(T1,T2), sameDelta(S1,S2,T1,T2).

% Matching transitions require no delta differences
sameDelta(S1,S2,T1,T2) :-
    transition(S1,S2),
    transition(T1,T2),
    not diffDelta(S1,S2,T1,T2).

% A difference in delta is observed if selected(C) and both deltas exist
diffDelta(S1,S2,T1,T2) :-
    transition(S1,S2),
    transition(T1,T2),
    select(C),
    delta(S1,S2,C,D1),
    delta(T1,T2,C,D2),
    D1 != D2.

% ============================================
% Value Function 
% ============================================

% Optimal value function V*(S): distance from a goal
dist(S,0) :- goal(S).
dist(S1,V+1) :- transition(S1,S2), dist(S2,V), V+1 <= maxdist.
v_star(S,N) :- N = #min{D : dist(S,D)}, state(S).
#const maxdist = 15.
poss_dist(0..maxdist).

#const delta = 2.
{v(S,D) : v_star(S,D_star), poss_dist(D), D_star <= D, D <= delta*D_star} = 1 :- state(S), live(S).
:- good(S1,S2), v(S1,D1), v(S2,D2), D1 <= D2.
