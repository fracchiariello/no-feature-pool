holds(S, (Pred, Arg1, Arg2), primitive) :- holds(S, (Pred, Arg1, Arg2)).

holds(S, (Pred, Arg2, Arg1), inverse) :- holds(S, (Pred, Arg1, Arg2)).

holds(S, (Pred, Arg1, Arg2), plus) :- holds(S, (Pred, Arg1, Arg2)).
holds(S, (Pred, Arg1, Arg2), plus) :- holds(S, (Pred, Arg1, Arg3), plus), holds(S, (Pred, Arg3, Arg2)).

%holds(S, ((Pred1,Pred2), Arg1, Arg2), intersection) :- holds(S, (Pred1, Arg1, Arg2)), holds(S, (Pred2, Arg1, Arg2)). 

%holds(S, ((Pred1,Pred2), Arg1, Arg2), union) :- holds(S, (Pred1, Arg1, Arg2)), role(Pred2). 
%holds(S, ((Pred1,Pred2), Arg1, Arg2), union) :- holds(S, (Pred2, Arg1, Arg2)), role(Pred1). 

%holds(S, (Pred, Arg1, Arg2), negation) :- not holds(S, (Pred, Arg1, Arg2)), object(Arg1), object(Arg2), state(S), role(Pred).

%holds(S, ((Pred1,Pred2), Arg1, Arg2), composition) :- holds(S, (Pred1, Arg1, Arg3)), holds(S, (Pred2, Arg3, Arg2)). 

%Objects
%object(Arg) :-
%    holds(_, (_, Arg)).
%object(Arg) :-
%    holds(_, (_, Arg, _)).
%object(Arg) :-
%    holds(_, (_, _, Arg)).

%States
%state(S) :- transition(S,_).
%state(S) :- transition(_,S).

%Roles
%role(R) :- holds(_,(R,_,_)).


%holds(S, (Pred, Arg1, Arg2), star) :- holds(S, (Pred, Arg1, Arg2), plus).
%holds(S, (Pred, Arg, Arg), star) :- object(Arg), state(S), role(Pred).

#show holds/3.