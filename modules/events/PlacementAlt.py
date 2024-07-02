
import time
import logging

from modules.Environment import Environment
from modules.EventQueue import EventQueue

from modules.resource.Application import Application
from modules.resource.Processus import Processus
from modules.resource.Path import Path

from modules.events.Event import Event
from modules.events.Undeploy import Undeploy
from modules.events.DeployProc import DeployProc

from modules.processing.OptimalNodeMapping import O_N_M
from modules.processing.OptimalLinkMapping import O_L_M

from modules.CustomExceptions import DeviceNotFoundError

from typing import Optional, Dict, Any, List

# TODO : Check these imports

import numpy as np
import random

import gurobipy as gp
from gurobipy import GRB


class BatchProcessing(Event):
    def __init__(self, event_name: str, queue: EventQueue, event_time: Optional[int]=None, next_batch: Optional['BatchProcessing'] = None):
        super().__init__(event_name, queue, event_time)

        if next_batch:
            self.next_batch = next_batch

        self.stack: List['PlacementAlt'] = list()


    @property
    def next_batch(self) -> 'BatchProcessing':
        return self._next_batch

    @next_batch.setter
    def next_batch(self, next_batch: 'BatchProcessing') -> None:
        self._next_batch = next_batch

    def add_to_batch(self, placement_event: 'PlacementAlt'):
        self.stack.append(placement_event)
        logging.debug(f"Current Time : {placement_event.time}, added placement_event : {placement_event.application_to_place.id} on device {placement_event.deployment_starting_point}")

    def process(self, env):
        self.new_process(env)

    def new_process(self, env):
        logging.debug(f"\n ######### \n Batch Processing \n Time : {self.time} \n")
        logging.debug(f"self.stack is {[item.application_to_place.id for item in self.stack]}")

        num_dev = len(env.devices)
        logging.debug("num_dev ", num_dev)
        comp_app = [item.application_to_place.num_procs for item in self.stack]
        logging.debug("comp_app ", comp_app)
        num_comp = sum(comp_app)
        logging.debug("num_comp ", num_comp)
        num_app = len(self.stack)
        logging.debug("num_app ", num_app)
        dim = len(env.get_random_device().position)
        logging.debug("dim ", dim)
        num_resource = len(env.get_random_device().resource_limit)
        logging.debug("num_resource ", num_resource)

        pos_app = np.transpose(np.array([list(env.get_device_by_id(item.deployment_starting_point).position.values()) for item in self.stack]))
        logging.debug("pos_app", pos_app)

        pos_dev = np.transpose(np.array([list(device.position.values()) for device in env.devices]))
        logging.debug("pos_dev", pos_dev)

        pos_comp=np.array([[0 for col in range(num_comp)] for row in range(dim)], dtype=float)     #Position of all Comps of all Apps in 2D (m)
        c: int=0              #Counter used in iteration
        for i in range(num_app):
            for j in range(comp_app[i]):
                pos_comp[:,c+j]=pos_app[:,i]
            c = c + comp_app[i]
        logging.debug("pos_comp", pos_comp)

        cap_dev_nod = np.array([np.array(list(device.resource_limit.values())) - np.array(list(device.current_resource_usage.values())) for device in env.devices])
        logging.debug("cap_dev_nod", cap_dev_nod)

        cap_comp_nod = np.array([list(processus.resource_request.values()) for item in self.stack for processus in item.application_to_place.processus_list])
        logging.debug("cap_comp_nod", cap_comp_nod)

        app_dev_mxd = env.config.wifi_range
        logging.debug("app_dev_mxd", app_dev_mxd)


        cap_comp_lnk = np.array([[0 for col in range(num_comp)] for row in range(num_comp)], dtype=float)

        c: int=0              #Counter used in iteration
        for index, item in enumerate(self.stack):
            for i in range(comp_app[index]):
                for j in range(comp_app[index]):
                    cap_comp_lnk[c + i, c + j] = item.application_to_place.proc_links[i, j]
            c += comp_app[index]

        # Only tested on small range, might need to double check the index by hand
        logging.debug("cap_comp_lnk", cap_comp_lnk)

        cap_dev_lnk = env.physical_network.extract_available_bandwidth_matrix()
        cap_dev_lnk = np.where(np.isinf(cap_dev_lnk), 10000, cap_dev_lnk)
        logging.debug("cap_dev_lnk", cap_dev_lnk)
        # Same, untested, using previous placholder implementation for this specific case but should work out of the box

        LAPL=np.diag(np.transpose(np.dot(cap_comp_lnk, np.ones((num_comp, 1))))[0])-cap_comp_lnk

        start_time = time.time()

        comp_dev_asg, ZE = O_N_M(env, num_dev, num_comp, num_app, num_resource, pos_app, comp_app, pos_dev, cap_comp_nod, cap_dev_nod, cap_dev_lnk, app_dev_mxd, dim, LAPL)

        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"O_N_M Elapsed time: {elapsed_time:.2f} seconds")


        start_time = time.time()

        hop_max = 3
        cst_max = 40
        f_max = max(max(cap_dev_lnk, key=max))                                                      #Upper bound on throughput of PHY-NET links


        yy_sol, zz_sol, ff_sol, ALL_PA, MFFM, fil_MF, MF, num_app2, numlnk, Cnumlnk = O_L_M(env, num_dev, num_app, pos_app, \
                                                                                    comp_app, pos_dev, cap_comp_lnk, cap_dev_lnk, comp_dev_asg, hop_max, cst_max, f_max, ZE)

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"O_L_M Elapsed time: {elapsed_time:.2f} seconds")


        OLM_RES1 = {s:[] for s in range(num_app2)}
        # OLM_RES2 = {s:[] for s in range(num_app2)}
        OLM_RES2 = {s:[] for s in range(len(MFFM))}
        FRR ={s:[] for s in range(num_app2)}
        

        ct =0
        ONM_RES={i:[] for i in range(num_app)}
        ONM_TEX={i:[] for i in range(num_app)}
        for s, item in enumerate(self.stack):
            b=0
            bb=[]
            for u in range(ZE[s], ZE[s+1]):
                for i in range(num_dev):
                    if comp_dev_asg[i][u]==1:
                        b += 1
                        bb.append(i)
            ONM_RES[s]=bb
            if b == comp_app[s]:
                ct += 1
                logging.debug(f"{comp_app[s]} Comp(s) of App {s} are deployed on Dev(s) {bb} in O-N-M step (Partial-S)")

                for deployment_index in range(len(bb)):
                    DeployProc("Deployment Proc", self.queue, item.application_to_place, bb, {None: None}, deployment_index, event_time=int((self.time+10)/10)*10, last=(deployment_index+1==len(bb))).add_to_queue()

                ONM_TEX[s]=str(comp_app[s])+" Comp(s) of App "+str(s)+" are deployed on Dev(s) "+str(bb)+" in O-N-M step (Partial-S)"

                ## FYI, debug, TODO remove this
                if item.tentatives != 1:
                    logging.debug(f"App {item.application_to_place.id} was finally accepted after {item.tentatives} tentatives")
            else:
                logging.debug(f"App {s} with {comp_app[s]} Comps failed in O-N-M step (Total-F)")
                ONM_TEX[s]=str(comp_app[s])+" Comp(s) of App "+str(s)+" failed to be deployed in O-N-M step (Total-F)"

                # Backoff handling

                if item.tentatives >= 15:
                    self.update_app_rejected(env)
                    self.update_app_waiting(env, -1)
                    logging.debug(f"App {item.application_to_place.id} was rejected after 15 failures")
                else:
                    item.tentatives +=1
                    self.next_batch.add_to_batch(item)


        oo=0
        for s in range(num_app2):
            if zz_sol[s][0]==0:
                FRR[s]= "App "+str(self.stack[fil_MF[s][0][0]].application_to_place.id)+" fails to pass O-L-M (Total-F)"
                OLM_RES1[s] = "App "+str(self.stack[fil_MF[s][0][0]].application_to_place.id)+" fails to pass O-L-M (Total-F)"
                print(f"App {str(self.stack[fil_MF[s][0][0]].application_to_place.id)} fails to pass O-L-M (Total-F)")
                for i in range(len(fil_MF[s])):
                    OLM_RES2[i+Cnumlnk[s]]=""

        logging.debug(f"{ct} of {num_app} Apps successfully passed O-N-M step with Acceptance Ratio(%) of O-N-M= {round(ct/num_app*100, 2)}")
        self.update_app_waiting(env, -ct)

    def old_process(self, env):
        logging.debug(f"\n ######### \n Batch Processing \n Time : {self.time} \n")
        logging.debug(f"self.stack is {[item.application_to_place.id for item in self.stack]}")

        prob = gp.Model(env=env.math_env)

        num_dev = len(env.devices)
        logging.debug("num_dev ", num_dev)
        comp_app = [item.application_to_place.num_procs for item in self.stack]
        logging.debug("comp_app ", comp_app)
        num_comp = sum(comp_app)
        logging.debug("num_comp ", num_comp)
        num_app = len(self.stack)
        logging.debug("num_app ", num_app)
        dim = len(env.get_random_device().position)
        logging.debug("dim ", dim)
        num_resource = len(env.get_random_device().resource_limit)
        logging.debug("num_resource ", num_resource)

        pos_app = np.transpose(np.array([list(env.get_device_by_id(item.deployment_starting_point).position.values()) for item in self.stack]))
        logging.debug("pos_app", pos_app)

        pos_dev = np.transpose(np.array([list(device.position.values()) for device in env.devices]))
        logging.debug("pos_dev", pos_dev)

        pos_comp=np.array([[0 for col in range(num_comp)] for row in range(dim)], dtype=float)     #Position of all Comps of all Apps in 2D (m)
        c: int=0              #Counter used in iteration
        for i in range(num_app):
            for j in range(comp_app[i]):
                pos_comp[:,c+j]=pos_app[:,i]
            c = c + comp_app[i]
        logging.debug("pos_comp", pos_comp)

        cap_dev_nod = np.array([np.array(list(device.resource_limit.values())) - np.array(list(device.current_resource_usage.values())) for device in env.devices])
        logging.debug("cap_dev_nod", cap_dev_nod)

        cap_comp_nod = np.array([list(processus.resource_request.values()) for item in self.stack for processus in item.application_to_place.processus_list])
        logging.debug("cap_comp_nod", cap_comp_nod)

        app_dev_mxd = env.config.wifi_range
        logging.debug("app_dev_mxd", app_dev_mxd)


        cap_comp_lnk = np.array([[0 for col in range(num_comp)] for row in range(num_comp)], dtype=float)

        c: int=0              #Counter used in iteration
        for index, item in enumerate(self.stack):
            for i in range(comp_app[index]):
                for j in range(comp_app[index]):
                    cap_comp_lnk[c + i, c + j] = item.application_to_place.proc_links[i, j]
            c += comp_app[index]

        # Only tested on small range, might need to double check the index by hand
        logging.debug("cap_comp_lnk", cap_comp_lnk)

        cap_dev_lnk = env.physical_network.extract_available_bandwidth_matrix()
        cap_dev_lnk = np.where(np.isinf(cap_dev_lnk), 10000, cap_dev_lnk)
        logging.debug("cap_dev_lnk", cap_dev_lnk)
        # Same, untested, using previous placholder implementation for this specific case but should work out of the box

        LAPL=np.diag(np.transpose(np.dot(cap_comp_lnk, np.ones((num_comp, 1))))[0])-cap_comp_lnk



        ################################# Workload-Placement (VNE) by sequential solving of Optimal-Node-Mapping (O-N-M) and Optimal-Link-Mapping (O-L-M) 
        ################################# (1) Formulating O-N-M as an IQP using Gurobi solver

        ######################################### Definition of function O_N_M for Optimal-Node-Mapping
        #def O_N_M(num_dev, num_comp, num_app, pos_app, comp_app, cap_comp_nod, cap_dev_nod, app_dev_mxd):


        ######################################### Definition of a number of parameters which are used later in the process of O-N-M formulation
        pos_comp=np.array([[0 for col in range(num_comp)] for row in range(dim)], dtype=float)     #Position of all Comps of all Apps in 2D (m)
        c: int=0              #Counter used in iteration
        for i in range(num_app):
            for j in range(comp_app[i]):
                pos_comp[:,c+j]=pos_app[:,i]
            c = c + comp_app[i]


        ZE=np.array([0 for col in range(num_app+1)], dtype=int)   #Same as vector gamma in my formulation
        c: int=0              #Counter used in iteration
        for i in range(num_app):
            c = c + comp_app[i]
            ZE[i+1]=c

        ########################################## Formulating O-N-M
        # Decision Variables: 
        ##########################################
        x = {}
        for u in range(num_comp):
            for i in range(num_dev):
                x[u, i] = prob.addVar(vtype=GRB.BINARY, name="x[%d,%d]" % (u, i), lb=0, ub=1)  #INTEGER

        y = {}
        for s in range(num_app):
            y[s] = prob.addVar(vtype=GRB.BINARY, name="y[%d]" % (s), lb=0, ub=1)  #INTEGER

        # Cost Function:
        ##########################################
        prob.setObjective(gp.quicksum(y[j] for j in range(num_app)), sense=GRB.MAXIMIZE)

        # Constraints og O-N-M:
        ################################################
        for u in range(num_comp):
            prob.addConstr(gp.quicksum(x[u, i] for i in range(num_dev)) <= 1)


        for j in range(num_app):
            prob.addConstr(gp.quicksum(x[u, i] for u in range(ZE[j], ZE[j+1]) for i in range(num_dev)) == y[j]*comp_app[j])


        for i in range(num_dev):
            for u in range(num_comp):
                prob.addConstr(((pos_dev[0][i]-pos_comp[0][u])**2 + (pos_dev[1][i]-pos_comp[1][u])**2)*x[u, i] <= (app_dev_mxd**2))


        for i in range(num_dev):
            for k in range(num_resource):
                prob.addConstr(gp.quicksum(x[u, i]*cap_comp_nod[u][k] for u in range(num_comp)) <= cap_dev_nod[i][k])


        for i in range(num_dev):
            prob.addConstr(gp.quicksum(LAPL[u1][u2]*x[u1, i]*x[u2, i] for u1 in range(num_comp) for u2 in range(num_comp)) <=\
                            gp.quicksum(cap_dev_lnk[i][k] for k in range(num_dev)))

        ################################################
        prob.optimize()

        ################################################
        ####################### PRINT RESULTS

        comp_dev_asg=np.array([[0 for col in range(num_comp)] for row in range(num_dev)], dtype=float)
        for i in range(num_dev):
            for u in range(num_comp):
                if x[u, i].X == 1.0:
                    comp_dev_asg[i][u]=1

        ct =0
        ONM_RES={i:[] for i in range(num_app)}
        ONM_TEX={i:[] for i in range(num_app)}
        for s, item in enumerate(self.stack):
            b=0
            bb=[]
            for u in range(ZE[s], ZE[s+1]):
                for i in range(num_dev):
                    if comp_dev_asg[i][u]==1:
                        b += 1
                        bb.append(i)
            ONM_RES[s]=bb
            if b == comp_app[s]:
                ct += 1
                logging.debug(f"{comp_app[s]} Comp(s) of App {s} are deployed on Dev(s) {bb} in O-N-M step (Partial-S)")

                for deployment_index in range(len(bb)):
                    DeployProc("Deployment Proc", self.queue, item.application_to_place, bb, {None: None}, deployment_index, event_time=int((self.time+10*ct)/10)*10, last=(deployment_index+1==len(bb))).add_to_queue()

                ONM_TEX[s]=str(comp_app[s])+" Comp(s) of App "+str(s)+" are deployed on Dev(s) "+str(bb)+" in O-N-M step (Partial-S)"

                ## FYI, debug, TODO remove this
                if item.tentatives != 1:
                    logging.debug(f"App {item.application_to_place.id} was finally accepted after {item.tentatives} tentatives")
            else:
                logging.debug(f"App {s} with {comp_app[s]} Comps failed in O-N-M step (Total-F)")
                ONM_TEX[s]=str(comp_app[s])+" Comp(s) of App "+str(s)+" failed to be deployed in O-N-M step (Total-F)"

                # Backoff handling

                if item.tentatives >= 15:
                    self.update_app_rejected(env)
                    self.update_app_waiting(env, -1)
                    logging.debug(f"App {item.application_to_place.id} was rejected after 15 failures")
                else:
                    item.tentatives +=1
                    self.next_batch.add_to_batch(item)

        logging.debug(f"{ct} of {num_app} Apps successfully passed O-N-M step with Acceptance Ratio(%) of O-N-M= {round(ct/num_app*100, 2)}")
        self.update_app_waiting(env, -ct)

    def update_app_waiting(self, env, value = 1):
        env.data.integrity_check(self.time)
        env.data.update_data(self.time, 'app_in_waiting', value)

    def update_app_rejected(self, env, value = 1):
        env.data.integrity_check(self.time)
        env.data.update_data(self.time, 'cumulative_app_rejected', value)

class PlacementAlt(Event):

    MAX_TENTATIVES = 5
    REFERENCE_PRIORITY = 2.0
    FIFTEEN_MINUTES_BACKOFF = 15 * 60 * 1000


    def __init__(self, event_name: str, queue: EventQueue, app: Application, device_id: int, event_time: Optional[int]=None, associated_batch: Optional[BatchProcessing] = None):
        super().__init__(event_name, queue, event_time)
        self.application_to_place = app
        self.deployment_starting_point = device_id
        
        if associated_batch:
            self.associated_batch = associated_batch
            self.batch = associated_batch

        self.tentatives = 1

    @property
    def batch(self) -> BatchProcessing:
        return self._batch

    @batch.setter
    def batch(self, batch: BatchProcessing) -> None:
        self._batch = batch

    def __json__(self) -> Dict[str, Any]:
        """
        Serialize the Placement object into a JSON-serializable dictionary.

        Returns:
            Dict[str, Any]: A dictionary containing key-value pairs of the Placement object's attributes.
                            {
                                "placement_time": time of the placement,
                                "requesting_device": ID of the "Placement Request Receptor" device,
                                "application": Application object to be placed
                            }
        """
        return {
            "placement_time" : self.time,
            "requesting_device" : self.deployment_starting_point,
            "application" : self.application_to_place
        }


    def process(self, env: Environment):
        """
        Tries to place a multi-processus application from a given device.

        Really messy, code to clean

        Args:
            env : Environment
        Returns:
            Tuple[List[int], List[int]]: Deployment times and deployed onto devices (Device ID List)
        """

        logging.debug(f"Placement procedure from {self.deployment_starting_point}")

        if env.config is None:
            raise ValueError("Configuration not set")

        self.update_app_arrival(env)

        self.update_app_waiting(env)

        self.batch.add_to_batch(self)



    def update_app_arrival(self, env):

        env.data.integrity_check(self.time)

        env.data.update_data(self.time, 'cumulative_app_arrival', 1)


    def update_app_waiting(self, env, value = 1):

        env.data.integrity_check(self.time)

        env.data.update_data(self.time, 'app_in_waiting', value)

