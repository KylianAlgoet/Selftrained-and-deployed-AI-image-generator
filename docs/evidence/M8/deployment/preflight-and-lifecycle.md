# Deployment tooling — real output

**Date:** 2026-08-09 · **Milestone:** M8 (phase M8.5) · **Machine:** the validated RTX 4060 Laptop
**No GPU inference ran.** No model was loaded and no generation was executed. `pipeline_loaded`
stayed `false` throughout, and `allocated_mb` stayed `0.0`.

## `scripts/verify-weights.ps1`

```
DeckForge AI - production weight verification
checkpoint root: C:\Expert Lab\Selftrained-and-deployed-AI-image-generator

PASS  minimal-geometric  EXP-027 step 300  2d425838cce59adc...
PASS  ukiyo-e            EXP-028 step 600  52381b6052ad71f1...
PASS  retro-poster       EXP-029 step 300  70d2afbfb3c09aff...

All 3 production checkpoints verified.
EXIT: 0
```

All three match the gate-2 hashes recorded in `apps/api/styles.py` and DR-010, at 6 414 480 bytes
each. The script **queries those constants from the code** rather than restating them, so it cannot
certify a machine the service would then refuse to serve from.

## `scripts/preflight.ps1`

```
DeckForge AI - preflight
repository: C:\Expert Lab\Selftrained-and-deployed-AI-image-generator

PASS  Python virtual env           3.11 at .venv (3.11.0)
PASS  Python dependencies          torch 2.13.0+cu126, diffusers 0.39.0, fastapi 0.141.1
PASS  CUDA                         available - NVIDIA GeForce RTX 4060 Laptop GPU
PASS  nvidia-smi                   NVIDIA GeForce RTX 4060 Laptop GPU, 610.88, 8188 MiB
PASS  Node.js                      v24.18.0
PASS  Frontend dependencies        apps/web/node_modules present
PASS  API port 8000                free
PASS  Frontend port 5173           free
PASS  Preview port 4173            free
PASS  Production weights           all 3 adapters match their recorded sha256

PREFLIGHT PASSED - the demo can start.
EXIT: 0
```

`torch.cuda.is_available()` is a capability query. It initialises no pipeline and runs no
generation.

## `scripts/start-demo.ps1`

```
API ready - pid 8632, cuda True, guard enforced
Starting the frontend (npm run dev)...

  DeckForge AI is running at http://localhost:5173
  API pid 19700 - frontend pid 33008 - recorded in .run\demo.json
EXIT: 0
```

### `GET /api/health`

```json
{"status":"ok","pid":8632,"pipeline_loaded":false,"active_style":null,
 "generation_in_progress":false,"cuda_available":true,
 "device_name":"NVIDIA GeForce RTX 4060 Laptop GPU","device_total_mb":8187.5,
 "device_used_mb":1081.5,"allocated_mb":0.0,"single_worker_guard":"enforced"}
```

`allocated_mb: 0.0` with `pipeline_loaded: false` is the measured proof that **starting the service
costs no GPU memory** — lazy loading works as DR-011 describes. The 1081.5 MiB of `device_used_mb`
belongs to other processes on the desktop, not to this one.

### `GET /api/styles`

```
key                 outcome        run_id
minimal-geometric   PASS           EXP-027
ukiyo-e             PASS           EXP-028
retro-poster        PARTIAL PASS   EXP-029
```

`retro-poster` reports its PARTIAL PASS through the API, not only in the documentation.

## A finding: `--workers 1` starts TWO processes

Measured, and previously unrecorded anywhere in this project:

```
ProcessId  ParentProcessId
    19700            18508     <- uvicorn supervisor; loads no model
     8632            19700     <- the worker; serves requests and holds the pipeline
```

`uvicorn --workers 1` runs a supervisor **plus** one worker. Task Manager therefore shows two
`python.exe` processes during a demo.

**This does not contradict the single-worker requirement, and it is not a duplicated API.** There
is exactly one worker, and only the worker loads a model — which is why `allocated_mb` is 0.0 above
and why the memory analysis in DR-011 and EXP-034 is unaffected.

Two practical consequences, both now handled:

1. **`/api/health` reports the WORKER's pid (8632), which is not the pid `start-demo.ps1` launched
   (19700, the supervisor).** Anyone comparing the two would reasonably conclude something had gone
   wrong. Both the runbook and this record state it plainly.
2. **`stop-demo.ps1` must stop the tree, not the recorded PID.** Stopping only 19700 would leave
   the worker holding port 8000 — the exact orphan the port check is meant to prevent. It stops
   children first, then the parent.

Worth noting that M7's closure recorded "API pid 25748" from a manual run; that was the supervisor
too. The distinction simply had not come up before because nothing had needed to stop the pair
programmatically.

## `scripts/stop-demo.ps1`

```
DeckForge AI - stopping the demo
  API        pid 19700 stopped
  frontend   pid 33008 stopped

  port 8000  released
  port 5173  released
  port 4173  released

All demo ports released.
EXIT: 0
```

Verified afterwards: **no `python.exe` or `node.exe` process matching `uvicorn` or `vite`
remained.** The script stops only the PIDs it recorded and their children — never by process name,
because killing every `node.exe` on a developer's machine would be a worse bug than the leak it was
cleaning up.

## The check that matters most

`start-demo.ps1` **refuses to start** when port 8000 is already held, printing the owning PID and
process name.

`config.assert_single_worker` cannot catch this case: it reads worker-count environment variables
inside one process, and nothing inside one process can see another that someone started in a
different terminal. Two resident pipelines do not fit in 8 GB, so without this check the first
symptom of a duplicated terminal would be a CUDA OOM in whichever request happened to be running —
mid-demonstration.

M7 closed by *manually* confirming both ports were released and no duplicate uvicorn remained.
This turns that habit into a check.
