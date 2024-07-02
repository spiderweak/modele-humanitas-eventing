import copy

import numpy as np
import gurobipy as gp

from gurobipy import GRB


def O_L_M(env, num_dev, num_app, pos_app, comp_app, pos_dev, cap_comp_lnk, cap_dev_lnk, comp_dev_asg, hop_max, cst_max, f_max, ZE):
    
    prob = gp.Model(env=env.math_env)

    def mwdfs(dgraph, wgraph, source, destin, visited, path, all_paths, hop, hop_max, cost, cost_max):
        visited[source] = True
        path.append(source)

        gg=0
        for k in range(len(path)-1):
            gg += wgraph[path[k]][path[k+1]]
        cost = np.round(gg, 2)

        if source == destin and hop<=hop_max and cost<=cost_max:        
            all_paths.append(path.copy())
            all_paths.append(hop)
            ff = path
            gg=0
            for k in range(len(ff)-1):
                gg += wgraph[ff[k]][ff[k+1]]
            
            all_paths.append(cost)           
        else:
            hop += 1 
            for neighbor, xx in dgraph.get(source, []):        
                if not visited[neighbor]:
                    mwdfs(dgraph, wgraph, neighbor, destin, visited, path, all_paths, hop, hop_max, cost, cost_max)    

        path.pop()
        visited[source] = False
        hop -= 1
        gg=0
        for k in range(len(path)-1):
            gg += wgraph[path[k]][path[k+1]]
        cost = np.round(gg, 2)   

    ###################################################################################    
    ############## function to Convert Array representation of Graph into Dict representation   
    def dict_graph(weight):
        dim= len(weight)
        dgraph = {i:[] for i in range(dim)} 
        for i in range(dim):
            for j in range(dim):
                if weight[i][j]>0:
                    dgraph[i].append((j, weight[i][j]))
        return dgraph

    ###################################################################################    
    ############## function to Convert Dict representation of Graph into Array representation    
    def arr_graph(dgraph):
        graphr = np.array([[0 for col in range(len(dgraph))] for row in range(len(dgraph))], dtype=float)
        for node in dgraph:
            for nn in range(len(dgraph.get(node, []))) :
                graphr[node][dgraph.get(node)[nn][0]]=dgraph.get(node)[nn][1]
        return graphr

    ###################################################################################     
    ############## function to Find All Paths from source to destin subject to upper-bounds hop_max and cost _max on their hop-count and sum-cost 
    def find_all_paths(dgraph, wgraph, source, destin, hop_max, cost_max):
        visited = {node: False for node in dgraph}
        all_paths = []
        path = []
        hop = 0
        cost = 0
        # weight = []
        mwdfs(dgraph, wgraph, source, destin, visited, path, all_paths, hop, hop_max, cost, cost_max)
        return all_paths

    #################################################################################################### 
    ############################## [1] PRE-PROCESSING step to solve O-L-M ############################## 
    SS ={i:[] for i in range(num_app)}   # Output of ONM step used in Link-Mapping step (before deleting co-locations for Comps of Apps with c>1 in OLM step)

    for j in range(num_app):
        if comp_app[j]>1:
            for k in range(ZE[j], ZE[j+1]):
                l=0
                D=True
                while D and (l<=num_dev-1):  #Search for 1 in column of O-N-M assignment matrix 
                    if comp_dev_asg[l][k]==1:                    
                        SS[j].append(l) 
                        D=False
                    else:
                        l+=1

    MF={i:[] for i in range(num_app)}    # Output of ONM step after deleting co-located vir-links for Apps with c>1 and bringing dummy phy-node effect for repeated requests
    for j in range(num_app):
        if comp_app[j]>1:
            WL=cap_comp_lnk[ZE[j]:ZE[j+1], ZE[j]:ZE[j+1]]
            FF=[]
            for i1 in range(np.size(WL, 0)-1):
                for i2 in range(i1+1, np.size(WL, 1)):
                    if WL[i1, i2]!=0:
                        FF.append(WL[i1, i2])
            for i3 in range(len(SS[j])-1):
                if (SS[j][i3]!=SS[j][i3+1] and i3==0):
                    MF[j].append([j, SS[j][i3], SS[j][i3+1], FF[i3]])
                elif (i3>0 and SS[j][i3]!=SS[j][i3+1]):
                    ii=-1
                    for i4 in range(len(MF[j])):
                        if all(np.sort([SS[j][i3], SS[j][i3+1]])==np.sort([MF[j][i4][1], MF[j][i4][2]]))==True:
                            ii=i4
                            break
                    if ii==-1:
                        MF[j].append([j, SS[j][i3], SS[j][i3+1], FF[i3]])
                    else:
                        MF[j][ii]=[j, MF[j][ii][1], MF[j][ii][2], (MF[j][ii][3]+FF[i3])]

    fil_MF={}               # A shortened version of MF after getting rid of all Apps that do not need OLM anymore
    nk=0
    for j, MF[j] in MF.items():
        if MF[j]!=[]:
            fil_MF[nk] = MF[j]
            nk += 1

    numlnk=[]
    for i, v in fil_MF.items():
        numlnk.append(len(v)-1)
    MFF={}                 # A modified version of MF after separating vir-link mapping requests of Apps with more than one request in distinct rows 
    for j, fil_MF[j] in fil_MF.items():
        sv = np.sum(numlnk[:j])
        i=0
        for i, val in enumerate(fil_MF[j]):
            new_key = int(i)+int(j)+int(sv)  # Create a new key using the original key and index
            MFF[new_key] = val               # Assign the single value to the new key
    MFF={key: [value[0]] + sorted([value[1], value[2]]) + [value[3]] for key, value in MFF.items()}
    MFS=copy.deepcopy(MFF)

    ########################## Remove all multiplicities out of Source-Destination Pairs in MFF by forming DUMMY-PHY-NODES and building new MFFM
    cc=0
    MFFM=copy.deepcopy(MFF) # A modified version of MFF after replacing repeated source-destination requests in PHY-NET with dummy PHY-Nodes 
    SQQ=cap_dev_lnk.copy() 
    for i in range(len(MFF)):
        for j in range(i+1, len(MFFM)):
            if list(np.sort([MFF[i][1], MFF[i][2]]))==list(np.sort([MFFM[j][1], MFFM[j][2]])):    
                MFFM[j][1]= num_dev + (cc)
                MFFM[j][2]= num_dev + (cc+1)
                cc+=2

                W = SQQ
                # Expand the array in size 
                cap_dev_lnk2 = np.zeros((np.size(W, 0)+2, np.size(W, 1)+2))
                # Evaluate the expanded array
                cap_dev_lnk2[:W.shape[0], :W.shape[1]] = W
                cap_dev_lnk2[MFFM[j][1]][MFF[i][1]]=f_max+1
                cap_dev_lnk2[MFF[i][1]][MFFM[j][1]]=f_max+1
                cap_dev_lnk2[MFFM[j][2]][MFF[i][2]]=f_max+1
                cap_dev_lnk2[MFF[i][2]][MFFM[j][2]]=f_max+1
                SQQ=cap_dev_lnk2             
    num_dev2=num_dev+cc     # Size of the modified PHY-NET after addition of Dummy-PHY-Nodes
    num_app2=len(fil_MF)    # Number of Apps that sucessfully passed ONM step and now require OLM for their final successful placement

    ## Same function as its counterpart array ZE in O-N-M)
    ZZ=np.array([0 for col in range(num_app2+1)], dtype=int)   
    c: int=0               
    for i in range(num_app2):
        c = c + numlnk[i] + 1
        ZZ[i+1]=c

    ## Relative Distance array of all Dev-Dev Pairs (to Define a type of Link-Cost)
    W=np.array([[0 for col in range(num_dev)] for row in range(num_dev)], dtype=float)     
    for i in range(num_dev):
        for j in range(num_dev):
            if cap_dev_lnk[i][j]>0:
                W[i,j]=np.round(np.linalg.norm(pos_dev[:, i] - pos_dev[:, j]), 2)

    ## Modified version of W after addition of Dummy-PHY-Nodes
    WM = np.zeros((np.size(W, 0)+(num_dev2-num_dev), np.size(W, 1)+(num_dev2-num_dev)))
    WM[:W.shape[0], :W.shape[1]] = W
    for i in range(num_dev2):
        for j in range(num_dev2):
            if SQQ[i, j]==f_max+1:
                WM[i][j]=1

    ## Modified HOP array and Modfied Cost MAX array after addition of Dummy-PHY-Nodes and their corresponding added Dummy-PHY-Links in WM
    HOPM = np.array([0 for col in range(len(MFFM))], dtype=int)
    CMAX = np.array([0 for col in range(len(MFFM))], dtype=float)
    for i in range(len(MFFM)):
        if MFFM[i][1]<num_dev and MFFM[i][2]<num_dev:
            HOPM[i]=hop_max
            CMAX[i]=cst_max
        else:
            HOPM[i]=hop_max+2
            CMAX[i]=cst_max+2

    ################# FINDING all Eligible Paths for all Needed Pairs of PHY-NODES found in MFF (after getting rid of all the repetitions) based on output of O-N-M
    ALL_PA ={}        ##Dict containing All Paths 
    wgraph = WM.copy()
    dgraph = dict_graph(wgraph)
    for i, v in MFFM.items():
        XX=find_all_paths(dgraph, wgraph, v[1], v[2], HOPM[i], CMAX[i])
        ALL_PA[i]=XX

    FF={i:[] for i in range(len(ALL_PA))}    #Dict containing maximum throughput value each path in ALL_PA can carry
    for i,v in ALL_PA.items():
        for j in range(len(v)):
            if j%3==0:
                ss=f_max
                for k in range(len(v[j])-1): 
                    if v[j][k]<num_dev and v[j][k+1]<num_dev:
                        ss = min(ss, cap_dev_lnk[v[j][k]][v[j][k+1]])
                FF[i].append(ss)


    Cnumlnk=[]                               #Delta vector in original formulation
    for i in range(len(numlnk)+1):
        Cnumlnk.append(int(np.sum(numlnk[:i])+len(numlnk[:i])))

    ################# Binary-PHYNET-Adjacency-Matrix of each Path in dict ALL_PA is generated as an Upper-Triangular Binary matrix of size num_dev * num_dev 
    PP={i:[] for i in range(len(ALL_PA))}    #dict containing Binary-PHYNET-Adjacency-Matrix of each path in ALL_PA dict
    for i,v in ALL_PA.items():
        for j in range(len(v)):
            if j%3==0:
                qq=np.array([[0 for col in range(num_dev)] for row in range(num_dev)], dtype=np.uint8)
                for k in range(len(v[j])-1):
                    if v[j][k]<num_dev and v[j][k+1]<num_dev:
                        pp=np.sort([v[j][k], v[j][k+1]])
                        qq[pp[0], pp[1]]=1
                PP[i].append(qq)
    ##############################################################################################

    ############################## [2] OPTIMIZATION step to solve O-L-M using GUROBI ############################## 
    probb = gp.Model(env=env.math_env)

    # Decision Variables: 
    ##########################################
    ff = {}
    for i in range(len(ALL_PA)):
        ff[i]={}
        for j in range(int(len(ALL_PA[i])/3)):
            ff[i][j] = probb.addVar(vtype=GRB.CONTINUOUS, name="ff[%d,%d]" % (i, j), lb=0, ub=FF[i][j])

    zz = {}
    for s in range(num_app2):
        zz[s] = probb.addVar(vtype=GRB.BINARY, name="zz[%d]" % (s), lb=0, ub=1)  


    yy = {}
    for s in range(len(MFFM)):
        yy[s] = probb.addVar(vtype=GRB.BINARY, name="yy[%d]" % (s), lb=0, ub=1)  


    # Cost Function:
    ##########################################
    probb.setObjective(gp.quicksum(zz[j]*len(fil_MF[j]) for j in range(num_app2)), sense=GRB.MAXIMIZE)


    # Constraints of O-L-M:
    ##########################################
    for j in range(num_app2):
        probb.addConstr(gp.quicksum(yy[k] for k in range(Cnumlnk[j], Cnumlnk[j+1])) == zz[j]*(numlnk[j]+1))


    for k in range(len(ALL_PA)):
        probb.addConstr(gp.quicksum(ff[k][m] for m in range(int(len(ALL_PA[k])/3))) == yy[k]*(MFFM[k][3]))


    for i in range(num_dev):
        for j in range(i+1, num_dev):
            if cap_dev_lnk[i][j]>0:
                probb.addConstr(gp.quicksum(ff[k][m]*PP[k][m][i, j] for k in range(len(ALL_PA)) for m in range(int(len(ALL_PA[k])/3))) <= cap_dev_lnk[i][j])

    ##########################################
    probb.optimize()

    ############################## [3] POST-PROCESSING step to solve O-L-M ############################## 
    ###### Retreiving decision variables after solving optimization and getting rid of Dummy-PHY-Nodes
    vars_list = probb.getVars()
    ff_sol = {i:[] for i in range(len(ALL_PA))}
    zz_sol = {i:[] for i in range(num_app2)}
    yy_sol = {i:[] for i in range(len(MFFM))}
    for var in vars_list:
        for i in range(len(ALL_PA)):
            for j in range(int(len(ALL_PA[i])/3)):
                if var.VarName=="ff[%d,%d]" % (i, j):
                    ff_sol[i].append(np.round(var.x, 2))
        for s in range(num_app2):
            if var.VarName=="zz[%d]" % (s):
                zz_sol[s].append(int(var.x))
        for s in range(len(MFFM)):
            if var.VarName=="yy[%d]" % (s):
                yy_sol[s].append(int(var.x))

    return yy_sol, zz_sol, ff_sol, ALL_PA, MFFM, fil_MF, MF, num_app2, numlnk, Cnumlnk
    ################################################
