state(S) :- transition(S,_).
state(S) :- transition(_,S).

%Primitive concept name
concept(P) :- holds(_,(P,_)).

%Initialization
concept(C, S, O, 0) :- holds(S,(C,O)). 

%Additional concept
%#const n=2. %number of additional concepts
concept("c1").
concept("c2").


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