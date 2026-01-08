% Optimal value function V*(S): distance from a goal
 dist(S,0) :- goal(S).
 dist(S1,V+1) :- transition(S1,S2), dist(S2,V), V+1 <= maxdist.
 v_star(S,N) :- N = #min{D : dist(S,D)}, state(S).
 #const maxdist = 20.
 poss_dist(0..maxdist).

% #const delta = 2.
 {v(S,D) : v_star(S,D_star), poss_dist(D), D_star <= D, D <= delta*D_star} = 1 :- state(S), live(S).
 :- good(S1,S2), v(S1,D1), v(S2,D2), D1 <= D2.