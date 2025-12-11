state(S) :- transition(S,_).
state(S) :- transition(_,S).

%Primitive concept name
concept(P) :- holds(_,(P,_)).

%Initialization
concept(C, S, O, 0) :- holds(S,(C,O)). 

%Additional concept
%#const n=0. %number of additional concepts
%concept(1..n).
%{concept(I, S, O, 0) : object(O) } = 1 :- state(S), I=1..n. 
%:- concept(I, S, O1, 0), concept(I, S, O2, 0), O1!=O2, I=1..n.

%Role
role(R) :- holds(_,(R,_,_)).

%objects
object(Arg) :-
    holds(_, (_, Arg)).
object(Arg) :-
    holds(_, (_, Arg, _)).
object(Arg) :-
    holds(_, (_, _, Arg)).


%Goal Reachability
live(G) :- goal(G).
live(S1) :- transition(S1, S2), live(S2).
%:- init(S), not live(S).