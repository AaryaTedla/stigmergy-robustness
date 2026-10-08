"""Auditable review fixtures, frozen-policy sensitivity and measured figures.

Run from the repository with pinned Python 3.12:
  python scripts/review_evidence.py sensitivity --root artifacts/review-eight
  python scripts/review_evidence.py figures --root artifacts/review-eight
Sensitivity loads only a completed, hash-validated NEW checkpoint, uses its
four declared development maps, and evaluates clean local observations with
food/home channels zeroed. Other channels and carrying/progress remain intact.
It saves per-step actions/delivery and counterfactual action differences on the
same local rows with paired Torch sampling RNG. Realized paired-trajectory
changes are also recorded. Neither measure is a trained no-pheromone baseline.

Figures uses completed comparison JSONL and exact scripted simulator arrays.
Scripted row-then-column routes use privileged coordinates and are mechanics
fixtures, NEVER PPO performance. States at 0/10/20/final are saved as JSON and
rendered with cell values. Clean/disabled fixtures must exactly match; selected
IDs match disabled/attack; all repeats must be identical. An additional old
2-agent route shows exhausted-patch waiting under the NEW home rule.

Plots report raw episode points, cumulative deliveries and injection mass,
and matched food-observation changes (not detector scores). Global/honest
accounting and identities are provenance only, never policy inputs. Outputs
are fresh subdirectories; old artifacts are never overwritten. Figures use
headless matplotlib, numeric rounding affects display only. Zero results and
negative paired effects are kept. This script does not tune maps or budgets.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import torch
from stable_baselines3 import PPO

from stigmergy.attacks import AttackConfig
from stigmergy.environment import GridConfig, ResourceRetrievalEnv
from stigmergy.training import policy_digest
from stigmergy.trajectories import _json_value, _git_provenance, matched_attack_configs


def save(path, value):
    """Serialize arrays without rounding; JSON is the source behind screenshots."""
    Path(path).write_text(json.dumps(_json_value(value), indent=2, sort_keys=True)+'\n')


def load_validated(root):
    """Accept final parameters only from completed matching-source training."""
    folder = root/'training'
    manifest = json.loads((folder/'manifest.json').read_text())
    summary = json.loads((folder/'summary.json').read_text())
    if manifest['status'] != 'completed' or not summary['checkpoint_roundtrip']:
        raise ValueError('completed reload-validated training is required')
    for name in ('environment.py','attacks.py','policies.py','ppo_adapter.py','training.py'):
        current = hashlib.sha256((Path('src/stigmergy')/name).read_bytes()).hexdigest()
        if current != manifest['source_sha256'][name]:
            raise ValueError(f'changed training source: {name}')
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    model = PPO.load(folder/'policy.zip', device='cpu')
    if policy_digest(model) != summary['final_parameter_sha256']:
        raise ValueError('checkpoint parameter hash differs')
    return model, GridConfig(**manifest['grid_config']), manifest


def zero_pheromone_rows(rows):
    """Copy (N,58) observations and zero ONLY food/home patch channels."""
    if rows.ndim != 2 or rows.shape[1] != 58:
        raise ValueError("expected (N,58) local observations")
    result = rows.copy()
    result[:, :54].reshape(-1,3,3,6)[:,:,:,2:4] = 0
    return result


def sensitivity(root):
    """Measure food/home observation ablation without retraining or defense."""
    model, grid, training = load_validated(root)
    comparison = json.loads((root/'comparison/manifest.json').read_text())
    if comparison['status'] != 'completed':
        raise ValueError('completed matched comparison required')
    output = root/'sensitivity'
    output.mkdir(exist_ok=False)
    manifest = {'status':'started', 'label':'frozen-policy observation sensitivity; NOT trained no-pheromone baseline',
                'grid_config':asdict(grid), 'checkpoint_parameter_sha256':policy_digest(model),
                'provenance':_git_provenance(), 'training_maps':training['training_config']['train_map_seeds'],
                'diagnostic_maps':comparison['comparison_config']['map_seeds'], 'groups':[]}
    save(output/'manifest.json', manifest)
    rows = []
    try:
        for group in comparison['groups']:
            world = ResourceRetrievalEnv(grid)
            observations, _ = world.reset(seed=group['map_seed'])
            folder = output/group['group_id']
            folder.mkdir()
            changed = denominator = 0
            baseline_actions = []
            for line in (root/'comparison/episodes'/group['group_id']/'clean/steps.jsonl').open():
                baseline_actions.append(json.loads(line)['local']['executed_actions'])
            trajectory_changed = trajectory_denominator = 0
            with (folder/'steps.jsonl').open('w') as stream, torch.random.fork_rng(devices=[]):
                torch.manual_seed(group['map_seed']+group['action_seed'])
                while world.agents:
                    agents = tuple(world.agents)
                    original = np.stack([observations[a] for a in agents])
                    zeroed = zero_pheromone_rows(original)
                    state = torch.get_rng_state()
                    full, _ = model.predict(original, deterministic=group['action_mode']=='deterministic')
                    torch.set_rng_state(state)
                    ablated, _ = model.predict(zeroed, deterministic=group['action_mode']=='deterministic')
                    changed += int(np.count_nonzero(full != ablated))
                    denominator += len(agents)
                    actions = dict(zip(agents,map(int,ablated)))
                    index = world.steps
                    if index < len(baseline_actions):
                        trajectory_changed += sum(actions[a] != baseline_actions[index][a] for a in agents)
                        trajectory_denominator += len(agents)
                    observations, _, _, _, _ = world.step(actions)
                    stream.write(json.dumps({'step':world.steps,'actions':actions,
                        'same_observation_full_actions':dict(zip(agents,map(int,full))),
                        'total_delivered':world.delivered_total})+'\n')
            baseline = json.loads((root/'comparison/episodes'/group['group_id']/'clean/episode.json').read_text())['metrics']
            row = {**{k:group[k] for k in ('group_id','map_seed','action_seed','action_mode')},
                   'full_delivered':baseline['total_delivered'], 'zeroed_delivered':world.delivered_total,
                   'delivery_difference_zeroed_minus_full':world.delivered_total-baseline['total_delivered'],
                   'same_observation_action_changes':changed,'same_observation_action_count':denominator,
                   'paired_trajectory_action_changes':trajectory_changed,
                   'paired_trajectory_overlap_action_count':trajectory_denominator}
            rows.append(row)
            save(folder/'episode.json',row)
            manifest['groups'].append(group)
            world.close()
        if policy_digest(model) != manifest['checkpoint_parameter_sha256']:
            raise RuntimeError('frozen checkpoint changed')
        result = {'episodes':rows,'by_mode':{mode:{
            'episode_count':sum(r['action_mode']==mode for r in rows),
            'full_mean':float(np.mean([r['full_delivered'] for r in rows if r['action_mode']==mode])),
            'zeroed_mean':float(np.mean([r['zeroed_delivered'] for r in rows if r['action_mode']==mode])),
            'same_observation_action_change_fraction':sum(r['same_observation_action_changes'] for r in rows if r['action_mode']==mode)/sum(r['same_observation_action_count'] for r in rows if r['action_mode']==mode),
            'paired_trajectory_action_change_fraction':sum(r['paired_trajectory_action_changes'] for r in rows if r['action_mode']==mode)/sum(r['paired_trajectory_overlap_action_count'] for r in rows if r['action_mode']==mode)}
            for mode in ('deterministic','stochastic')},'checkpoint_unchanged':True,
            'limitations':'One frozen policy, development maps; zeroing inputs is distribution shift, not trained baseline.'}
        save(output/'summary.json',result)
        manifest['status']='completed'
    except BaseException as error:
        manifest.update(status='incomplete' if isinstance(error,KeyboardInterrupt) else 'failed',error=str(error))
        raise
    finally:
        save(output/'manifest.json',manifest)


def state(world):
    """Capture global arrays solely for human mechanics screenshots."""
    return {'step':world.steps,'positions':world.positions.copy(),'food':world.food.copy(),
            'nest':world.nest.copy(),'fields':world.fields.copy(),'carrying':world.carrying.copy(),
            'steps_since_nest':world.steps_since_nest.copy(),'delivered':world.delivered_total,
            'remaining':int(world.food.sum()),'carried':int(world.carrying.sum())}


def scripted(grid, attack):
    """Known-coordinate fixture; row-first return, never a learned baseline."""
    world = ResourceRetrievalEnv(grid,attack_config=attack)
    patches = [(1,grid.size-1),(grid.size-2,grid.size-1)]
    world.reset(seed=7,options={'food_positions':patches})
    states = [state(world)]
    steps = []
    waiting = []
    while world.agents:
        actions = {}
        for i, agent in enumerate(world.agents):
            target = (1,1) if world.carrying[i] else patches[i%2]
            r,c = world.positions[i]
            actions[agent] = 3 if r<target[0] else 1 if r>target[0] else 2 if c<target[1] else 4 if c>target[1] else 0
        world.step(actions)
        states.append(state(world))
        steps.append({'step':world.steps,'actions':actions,'delivered':world.delivered_total,
                      'attack_events':[e.as_dict() for e in world.last_attack_events]})
        if not world.carrying[0] and tuple(world.positions[0])==patches[0] and world.food[patches[0]]==0:
            waiting.append({'step':world.steps,'home':float(world.fields[(1,*patches[0])]),'action':actions['agent_0']})
    return states,steps,waiting,world.attack_summary()


def screenshot(snapshot, label, output, n_agents, k):
    """Draw exact 8×8 global state; one-decimal field values are display rounding."""
    fields = np.asarray(snapshot['fields']); positions=np.asarray(snapshot['positions'])
    food=np.asarray(snapshot['food']); nest=np.asarray(snapshot['nest'])
    fig, axes=plt.subplots(1,3,figsize=(14,4.9))
    grid = nest.astype(float)
    grid[food>0]=2
    axes[0].imshow(grid,cmap=matplotlib.colors.ListedColormap(['#f4f6f9','#cfdfef','#b4e4bf']),vmin=0,vmax=2)
    for r in range(8):
        for c in range(8):
            occupants=np.where(np.all(positions==(r,c),axis=1))[0]
            text=('N' if nest[r,c] else f'F{food[r,c]}' if food[r,c] else '')
            if len(occupants): text += ('\n' if text else '')+f'A×{len(occupants)}'
            axes[0].text(c,r,text,ha='center',va='center',fontsize=10)
    axes[0].set_title('Nest / remaining food / agent count')
    for ch,title in [(0,'Food pheromone'),(1,'Home pheromone')]:
        ax=axes[ch+1]; ax.imshow(fields[ch],cmap='Greens' if ch==0 else 'Blues',vmin=0,vmax=9)
        for r in range(8):
            for c in range(8):
                ax.text(c,r,f'{fields[ch,r,c]:.1f}',ha='center',va='center',fontsize=9)
        ax.set_title(title+' (simulation units)')
    for ax in axes:
        ax.set_xticks(range(8)); ax.set_yticks(range(8)); ax.tick_params(labelsize=8)
        ax.set_xticks(np.arange(-.5,8),minor=True); ax.set_yticks(np.arange(-.5,8),minor=True)
        ax.grid(which='minor',color='#b9c9da',linewidth=.6); ax.tick_params(which='minor',bottom=False,left=False)
        ax.set_xlabel('column'); ax.set_ylabel('row')
    fig.suptitle(f'{label} | step {snapshot["step"]} | remaining {snapshot["remaining"]} | carried {snapshot["carried"]} | delivered {snapshot["delivered"]}',fontsize=14)
    fig.text(.5,.01,f'Scripted mechanics only | N={n_agents}, selected k={k} ({k/n_agents:.1%}) | actual arrays, rounded display | home decay=0.95; evaporation=10%',ha='center',fontsize=10)
    fig.tight_layout(rect=(0,.10,1,.93)); fig.savefig(output,dpi=160); plt.close(fig)


def figures(root):
    """Render fixtures and aggregate measured logs without selecting outcomes."""
    output=root/'figures'; output.mkdir(exist_ok=False)
    fixtures=root/'fixtures'; fixtures.mkdir(exist_ok=False)
    grid=GridConfig(**json.loads(Path('configs/env/review-eight.json').read_text()))
    attack=AttackConfig(**json.loads(Path('configs/attack/persistent-review.json').read_text()))
    fixture_records={}
    for scenario,chosen in matched_attack_configs(attack).items():
        result=scripted(grid,chosen)
        repeat=scripted(grid,chosen)
        if json.dumps(_json_value(result),sort_keys=True)!=json.dumps(_json_value(repeat),sort_keys=True):
            raise RuntimeError('scripted fixture repeat differs')
        states,steps,waiting,accounting=result
        fixture_records[scenario]=result
        folder=fixtures/scenario;folder.mkdir()
        for index in (0,10,20,len(states)-1):
            save(folder/f'state-{index}.json',states[index])
            screenshot(states[index],scenario.replace('_',' ').title(),output/f'{scenario}-step-{index}.png',8,0 if chosen is None else 1)
        with (folder/'steps.jsonl').open('w') as stream:
            for record in steps:stream.write(json.dumps(_json_value(record))+'\n')
        save(folder/'manifest.json',{'grid_config':asdict(grid),'scenario':scenario,'seed':7,
             'label':'scripted mechanics only','provenance':_git_provenance(),'selected_fraction':0 if chosen is None else .125,
             'attack_summary':accounting,'states_saved':[0,10,20,len(states)-1],
             'delivered':states[-1]['delivered'],'repeated_identically':True})
    if json.dumps(_json_value(fixture_records['clean'][0]))!=json.dumps(_json_value(fixture_records['injection_disabled'][0])):
        raise RuntimeError('clean/disabled fixture arrays differ')
    if fixture_records['injection_disabled'][3]['compromised_agents']!=fixture_records['attacked'][3]['compromised_agents']:
        raise RuntimeError('matched selected IDs differ')
    old_grid=GridConfig(**json.loads(Path('configs/env/development.json').read_text()))
    states,_,waiting,_=scripted(old_grid,None)
    save(fixtures/'waiting-diagnostic.json',{'grid_config':asdict(old_grid),'waiting':waiting,
        'label':'two-agent historical route with NEW mechanics; not the eight-agent PPO experiment'})
    # The first arrival is a successful movement and can deposit; all subsequent
    # waits must be pure evaporation even when the episode continues elsewhere.
    for previous,current in zip(waiting,waiting[1:]):
        if current['step']==previous['step']+1 and current['action']==0:
            assert np.isclose(current['home'],previous['home']*.9)
    fig,ax=plt.subplots(figsize=(9,4));ax.plot([v['step'] for v in waiting],[v['home'] for v in waiting],marker='o',markersize=3)
    ax.set(xlabel='World step: agent waits at exhausted upper food patch',ylabel='Home concentration (units)',title='Waiting outside the nest adds no home pheromone')
    ax.grid(alpha=.2);fig.text(.5,.01,'Two-agent scripted waiting diagnostic, new mechanics | recorded values decay by ×0.9 per wait; old hotspot was 8.7',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.06,1,1));fig.savefig(output/'waiting-decay.png',dpi=160);plt.close(fig)
    comparison=json.loads((root/'comparison/manifest.json').read_text())
    if comparison['status']!='completed':raise ValueError('comparison incomplete')
    cache={}
    for group in comparison['groups']:
        for scenario in comparison['scenarios']:
            path=root/'comparison/episodes'/group['group_id']/scenario/'steps.jsonl'
            values=[]
            for line in path.open():
                row=json.loads(line);local=row['local'];meta=row['simulator_metadata']
                obs=np.array(list(local['observations_before'].values()))
                events=meta['attack_events']
                values.append([meta['total_delivered'],meta['honest_delivered'],
                    sum(e['requested_mass'] for e in events),sum(e['applied_mass'] for e in events),
                    float(obs[:,:54].reshape(-1,3,3,6)[:,:,:,2].mean())])
            array=np.array(values); padded=np.zeros((grid.horizon,5));padded[:len(array)]=array
            padded[len(array):,:2]=array[-1,:2]
            # Completed episode has no new observations afterwards; use NaN.
            padded[len(array):,4]=np.nan
            cache[group['group_id'],scenario]=padded
    colors=['#168d83','#b44d52','#638bac','#9178a7','#ed9b36','#4a5064']
    fig,axes=plt.subplots(1,2,figsize=(14,5))
    for ax,mode in zip(axes,['deterministic','stochastic']):
        groups=[g['group_id'] for g in comparison['groups'] if g['action_mode']==mode]
        for scenario,color in zip(comparison['scenarios'],colors):
            mean=np.mean([cache[g,scenario][:,0] for g in groups],axis=0)
            ax.plot(range(1,grid.horizon+1),mean,label=scenario.replace('_',' '),color=color)
        ax.set(title=mode.capitalize(),xlabel='World step',ylabel='Mean cumulative team deliveries',ylim=(0,8.3));ax.grid(alpha=.2)
    axes[-1].legend(fontsize=8);fig.suptitle('Frozen PPO delivery over time: every matched scenario')
    fig.text(.5,.01,'N=8, k=1 (12.5%) in disabled/attack | 4 deterministic + 12 stochastic episodes per scenario | one training seed; development only',ha='center',fontsize=10)
    fig.tight_layout(rect=(0,.05,1,.95));fig.savefig(output/'delivery-over-time.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(13,8))
    for col,mode in enumerate(['deterministic','stochastic']):
        groups=[g['group_id'] for g in comparison['groups'] if g['action_mode']==mode]
        for scenario,color in [('attacked','#168d83'),('attacked_timeout','#b44d52')]:
            for field,style,label in [(2,'--','requested'),(3,'-','applied')]:
                mean=np.mean([np.cumsum(cache[g,scenario][:,field]) for g in groups],axis=0)
                axes[0,col].plot(range(1,501),mean,style,color=color,label=scenario+' '+label)
        axes[0,col].set(title=mode.capitalize(),xlabel='World step',ylabel='Mean cumulative injection mass');axes[0,col].legend(fontsize=8)
        diff=np.array([cache[g,'attacked'][:,4]-cache[g,'injection_disabled'][:,4] for g in groups])
        for values in diff:axes[1,col].plot(range(1,501),values,color='#91b8b2',alpha=.4,lw=.8)
        axes[1,col].plot(range(1,501),np.nanmean(diff,axis=0),color='#168d83',label='paired mean')
        axes[1,col].axhline(0,color='gray',lw=.7)
        axes[1,col].set(xlabel='World step',ylabel='Attacked − disabled local food channel mean');axes[1,col].legend(fontsize=8)
        for row in range(2):axes[row,col].grid(alpha=.2)
    fig.suptitle('Injection accounting and locally observed field changes')
    fig.text(.5,.01,'N=8, k=1 (12.5%) | food channels normalized by cap=10 | observation changes, NOT detector scores or confirmed harmful exposure',ha='center',fontsize=10)
    fig.tight_layout(rect=(0,.05,1,.95));fig.savefig(output/'mass-and-observations.png',dpi=160);plt.close(fig)
    training=json.loads((root/'training/summary.json').read_text())
    fig,axes=plt.subplots(1,2,figsize=(10,4.5))
    for ax,mode in zip(axes,['deterministic','stochastic']):
        samples=[[e['delivered'] for e in training[phase][mode]['episodes']] for phase in ['before','after']]
        means=[np.mean(s) for s in samples];ax.bar([0,1],means,color=['#9aaabe','#168d83'])
        for x,vals in enumerate(samples):
            ax.scatter(x+np.linspace(-.13,.13,len(vals)),vals,color='#27354b',zorder=3)
            ax.text(x,means[x]+.15,f'{means[x]:.2f}',ha='center')
        ax.set(xticks=[0,1],xticklabels=['Initial policy','Fresh trained policy'],ylim=(0,8.7),ylabel='Team food delivered',title=mode.capitalize());ax.grid(axis='y',alpha=.2)
    fig.suptitle('Fresh PPO diagnostics: before / after training')
    fig.text(.5,.01,f'N=8 | {training["actual_agent_transitions"]:,} transitions | 4 maps × action seed 7 | dots: episodes | one training seed',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,.93));fig.savefig(output/'ppo-before-after.png',dpi=160);plt.close(fig)
    episodes=training['training_episodes']
    transitions=np.cumsum([e['steps']*grid.n_agents for e in episodes])
    deliveries=np.array([e['delivered'] for e in episodes])
    fig,ax=plt.subplots(figsize=(10,4))
    ax.scatter(transitions,deliveries,s=16,alpha=.45,label='completed training episodes')
    if len(deliveries)>=10:
        ax.plot(transitions[9:],np.convolve(deliveries,np.ones(10)/10,mode='valid'),color='#168d83',label='10-episode rolling mean')
    ax.set(xlabel='Cumulative agent transitions at completed episode',ylabel='Team deliveries per training episode',ylim=(0,8.5),title='Fresh clean PPO training history')
    ax.legend();ax.grid(alpha=.2)
    fig.text(.5,.01,'N=8 | training maps 0–15 | one seed | moving average is descriptive; not held-out evaluation',ha='center',fontsize=10)
    fig.tight_layout(rect=(0,.05,1,1));fig.savefig(output/'training-deliveries.png',dpi=160);plt.close(fig)
    sensitivity_result=json.loads((root/'sensitivity/summary.json').read_text())
    fig,axes=plt.subplots(1,2,figsize=(10,4.5))
    for ax,mode in zip(axes,['deterministic','stochastic']):
        samples=[[r[field] for r in sensitivity_result['episodes'] if r['action_mode']==mode] for field in ['full_delivered','zeroed_delivered']]
        ax.bar([0,1],[np.mean(v) for v in samples],color=['#168d83','#8b80b0'])
        for x,values in enumerate(samples):ax.scatter(x+np.linspace(-.15,.15,len(values)),values,color='#27354b',s=18,zorder=3)
        ax.set(xticks=[0,1],xticklabels=['Full local observation','Pheromone channels zero'],ylim=(0,8.5),ylabel='Team deliveries',title=mode.capitalize())
        ax.grid(axis='y',alpha=.2)
    fig.suptitle('Frozen policy: pheromone input sensitivity')
    fig.text(.5,.01,'Same clean diagnostic maps/action seeds | N=8 | dots: episodes | NOT separately trained no-pheromone baseline',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,.93));fig.savefig(output/'pheromone-sensitivity.png',dpi=160);plt.close(fig)
    # Copy existing scientific figures into the presentation bundle.
    for name in ['delivery_comparison.png','paired_effects.png']:
        (output/name).write_bytes((root/'comparison'/name).read_bytes())
    save(output/'verification.json',{'fixtures_repeat_identically':True,'clean_disabled_arrays_equal':True,
        'selected_ids_match':True,'waiting_decay_verified':True,'grid_config':asdict(grid),
        'compromised_count':1,'compromised_fraction':.125,'comparison_episodes':len(comparison['groups'])*6,
        'source_revision':_git_provenance()})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['sensitivity','figures'])
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    {'sensitivity':sensitivity,'figures':figures}[args.command](args.root)
