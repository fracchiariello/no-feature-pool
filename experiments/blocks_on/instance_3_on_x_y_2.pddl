;; An example where A is above B with some block between the two of them
(define (problem BLOCKS-3-ON-X-Y)
(:domain BLOCKS)
(:objects A B C)
(:init (CLEAR A) (ONTABLE B) (ON A C) (ON C B) (HANDEMPTY))
(:goal (AND (ON A B)))
)
