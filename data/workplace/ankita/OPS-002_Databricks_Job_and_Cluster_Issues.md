# OPS-002: Databricks Job and Cluster Issues (synthetic analogue)

Owner: Data Platform Operations

SYNTHETIC document written for a university assignment. Not a real company runbook.

## Job fails: "Driver is up but is not responsive, likely due to GC"
- Meaning: the driver node ran out of memory and spent its time in garbage collection.
- Common causes: more input data than before (for example new source tables), collecting large data to the driver with collect() or toPandas(), or broadcasting a large table.
- Fix:
  1. Check whether input volume grew; review recent code or source changes.
  2. Remove collect()/toPandas() on large DataFrames; write results to a table instead.
  3. Move the job to a larger driver node type, then rerun.
  4. If it keeps failing, raise it with the job owner to optimise joins and partitioning.
- Priority: P2 if a production job fails but a rerun or workaround is possible; P1 if downstream business reports are empty (see OPS-003).

## Cluster will not start
- "Cloud provider quota exceeded": the subscription has hit its vCPU quota; try a smaller node type or raise a quota request.
- Init script failure: check the cluster event log; a recent change to the init script is the usual cause.

## Library conflicts
Pin library versions on the job cluster; avoid installing different versions of the same library at notebook and cluster level.

## Job runs slowly
Check the Spark UI for skewed tasks; enable autoscaling for variable loads; review partition counts after data growth.
