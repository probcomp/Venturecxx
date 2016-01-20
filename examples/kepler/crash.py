import bayeslite

from bdbcontrib import query
from vsgpm import VsGpm

bdb = bayeslite.bayesdb_open()
bayeslite.bayesdb_read_csv_file(bdb, 'data',
    '/home/fsaad/pcp/bayeslite/tester/arcsin/data.csv', header=True,
    create=True)

vsgpm = VsGpm()
bayeslite.bayesdb_register_metamodel(bdb, vsgpm)

query(bdb, '''
CREATE GENERATOR sd FOR data USING vsgpm(
    columns(
        x1 NUMERICAL, x2 NUMERICAL),
    program('
        ; constants.
        (assume mu (list 10 -10 0))
        (assume var (list 1 2 1))
        ; global latents.
        (assume n_cluster 3)
        (assume r
            (tag (quote global) (quote r)
                (symmetric_dirichlet .5 n_cluster)))
        ; row latents.
        (assume k (mem (lambda (rowid)
            (tag (quote rowid) (quote k)
                (categorical r)))))
        ; columns
        (assume x1
            (mem (lambda (rowid)
              (tag (quote rowid) (quote x1)
                (normal
                    (lookup mu (k rowid))
                    (lookup var (k rowid)))))))
        (assume x2
            (mem (lambda (rowid)
                (tag rowid (quote x2)
                    (poisson (add 1 (k 1)))))))
        (assume columns (list x1 x2))
        '));''')

query(bdb, 'INITIALIZE 10 MODELS FOR sd')
query(bdb, 'ANALYZE sd FOR 1 ITERATION WAIT')
query(bdb, 'SIMULATE x1 FROM sd LIMIT 2')
