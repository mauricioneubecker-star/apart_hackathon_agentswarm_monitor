import pandas as pd
d = pd.read_csv('/Users/mauricio/sim_local/apart_vx/sim_dataset/dataset/index.csv', low_memory=False)
s = d.split.astype(str)
n = d[s.str.startswith('night_') & ~s.str.startswith('night_vx')].copy()
def vc(c): return n[c].value_counts(dropna=False).to_dict()
for c in ['rounds','deadline_round','credits','pressure_level','release_freeze','manager_push','prohibition_form','persona_mix','n_impossible','mutation_mix','discoverability','channels','self_merge','persistent_share','sanctions','detection_probability','seed_type','seed_placement','model_mix','model_mix_type','max_messages_per_round','max_message_tokens','memory_window_rounds','decoys','injection_carrier','malicious_variants','malicious_first_onset','tech_lead','context_notice','merge_feed_ci','board_post','lenient_quarantine','seed_advocacy','edit_feedback','post_cut','shocks_list','push_offset','seed_status','dependency_resolution','topology','connectivity','escalation_policy','json_retry','n_glm-5.2','family','ranking','category','n_info_asym','pioneer_status','enforcer','sanction']:
    try: print(c, vc(c))
    except Exception as e: print(c, 'ERR', e)
print('family by split', n.groupby(['split','family']).size().to_dict())
print('models sums', {c: int(n[c].sum()) for c in ['n_qwen3.8-27b','n_qwen3.5-397b','n_gemma4-31b','n_gemma4-26b-a4b','n_glm-5.2']})
print('detect>0', (n.detection_probability>0).sum())
print('cut x credits', n.groupby(['deadline_round','credits']).size().to_dict())
