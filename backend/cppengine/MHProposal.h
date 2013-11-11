
#ifndef VENTURE___MHPROPOSAL_H
#define VENTURE___MHPROPOSAL_H

#include "Header.h"
#include "VentureValues.h"
#include "VentureParser.h"
#include "XRPCore.h"
#include "Utilities.h"

extern int MHid;

struct MHProposalResults {
  MHProposalResults(real logscore_PNew, real logscore_POld) // Should be in the MHProposal.h?
    : logscore_PNew(logscore_PNew),
      logscore_POld(logscore_POld)
  {
  
  }

  real logscore_PNew;
  real logscore_POld;
};

enum MHDecision { MH_DECLINED, MH_APPROVED };

bool VerifyOrderPattern(vector<size_t>&,
                        vector<size_t>&);

struct Node;

void DeleteNode(shared_ptr<Node>);

void DeleteBranch(shared_ptr<Node>, bool);

class VentureException__ForcedMHDecline : std::runtime_error {
public:
  VentureException__ForcedMHDecline();
};

void TouchNode(shared_ptr<Node> node, stack< shared_ptr<Node> >& touched_nodes, vector< shared_ptr<Node> >& touched_nodes2, int proposal_unique_id);


void AddToReevaluationQueue
(ReevaluationEntry& current_reevaluation,
 shared_ptr<ReevaluationResult> reevaluation_result,
 shared_ptr<ReevaluationParameters> reevaluation_parameters);
 
void PropagateNewValue
(set<ReevaluationEntry,
   ReevaluationOrderComparer>& reevaluation_queue,
 stack< shared_ptr<Node> >& touched_nodes,
 vector< shared_ptr<Node> >& touched_nodes2,
 ProposalInfo& this_proposal,
 shared_ptr<ReevaluationParameters>& reevaluation_parameters);
 
void FinalizeProposal
(MHDecision mh_decision,
 shared_ptr<ReevaluationParameters>& reevaluation_parameters);

real GetCreatingRandomChoices(vector< shared_ptr<Node> >& touched_nodes2, set< shared_ptr<NodeXRPApplication> >& creating_random_choices);
real GetDeletingRandomChoices(vector< shared_ptr<Node> >& touched_nodes2, set< shared_ptr<NodeXRPApplication> >& deleting_random_choices);

MHProposalResults MakeMHProposal(shared_ptr<NodeXRPApplication> principal_node, shared_ptr<VentureValue> proposing_value, shared_ptr< map<string, shared_ptr<VentureValue> > > random_database, bool forcing_not_collecting);

struct ProposalInfo : public boost::enable_shared_from_this<ProposalInfo> {
  size_t proposal_unique_id;
  bool request_to_terminate;
};

pair<real, real> AbsorbBranchProbability(shared_ptr<Node> first_node, shared_ptr<ReevaluationParameters> reevaluation_parameters);

void UnabsorbBranchProbability(shared_ptr<Node> first_node, shared_ptr<ReevaluationParameters> reevaluation_parameters);

void Enumerate(shared_ptr<NodeXRPApplication> principal_node);
void SliceSample(shared_ptr<NodeXRPApplication> principal_node);

#endif
