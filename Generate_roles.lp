holds(S, (Pred, Arg1, Arg2), standard) :- holds(S, (Pred, Arg1, Arg2)).

holds(S, (Pred, Arg1, Arg2), inverse) :- holds(S, (Pred, Arg2, Arg1)).

holds(S, (Pred, Arg1, Arg2), plus) :- holds(S, (Pred, Arg1, Arg2)).
holds(S, (Pred, Arg1, Arg2), plus) :- holds(S, (Pred, Arg1, Arg3), plus), holds(S, (Pred, Arg3, Arg2)).

holds(S, (Pred, Arg1, Arg2), star) :- holds(S, (Pred, Arg1, Arg2), plus).
holds(S, (Pred, Arg, Arg), star) :- object(Arg), state(S), role(Pred).


%objects
object(Arg) :-
    holds(_, (_, Arg)).
object(Arg) :-
    holds(_, (_, Arg, _)).
object(Arg) :-
    holds(_, (_, _, Arg)).

state(S) :- transition(S,_).
state(S) :- transition(_,S).

%Role
role(R) :- holds(_,(R,_,_)).

#show holds/3.