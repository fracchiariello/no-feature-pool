state(S) :- transition(S,_).
state(S) :- transition(_,S).

%Primitive concept name
concept(P) :- holds(_,(P,_)).

%Initialization
concept(C, S, O, 0) :- holds(S,(C,O)). 

%Nominal Concepts
{nominal_concept(N)} :- goal_object(N).
concept(N) :- nominal_concept(N).
concept(N, S, N, 0) :- state(S), nominal_concept(N).

%Nullary predicates
nullary(P) :-  holds(_,(P,)). 


%Additional concept
#script (python)
import clingo
def cname(i):
    return clingo.Function(f"add_c{i}")
#end.
#const n=0.
add_concept(C) :- I = 1..n, C = @cname(I).
concept(S) :- add_concept(S).

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

