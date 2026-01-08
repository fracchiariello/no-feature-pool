state(S) :- transition(S,_).
state(S) :- transition(_,S).

%Primitive concept name
concept(P) :- holds(_,(P,_)).

%Initialization
concept(C, S, O, 0) :- holds(S,(C,O)). 

%Additional concept
#script (python)
import clingo
def cname(i):
    return clingo.String(f"add_c{i}")
#end.
#const n = 2.
concept(S) :- I = 1..n, S = @cname(I).


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

#show concept/4.
#show value/3.
#show evaluation/3.
#show good/2.
#show delta/4.

#show select/1.
#show selectRule/3.
#show param/3.
#show boolean_feature/1.
#show numerical_feature/1.

