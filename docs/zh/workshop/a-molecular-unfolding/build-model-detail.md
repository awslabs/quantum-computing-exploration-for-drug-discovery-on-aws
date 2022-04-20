在量子分子展开的示例代码中，本方案在大量采用了原作者的框架的基础上做了一些修改。原作者使用的是HUBO优化函数，本方案使用的是绝对距离，如下所示。代码中的方法名为pre-calc。

$$ O(x_{ik}) = A\displaystyle\sum\limits_i (\displaystyle\sum\limits_{k=1}^d x_{ik}-1)^2 - \displaystyle\sum\limits_{a,b} |D_{ab} (\theta)| $$

## 模型代码

您可以打开文件**source/src/molecualr-unfolding/untiliy/QMUQUBO.py**查看该模型的源代码。

以下代码展示了如何初始化变量：

!!! Note "说明"

    以下代码展示了构建模型的想法。您也可以在源码中找到类似的代码。

![Var Init](../../images/var-init.png)

图 8: 初始化变量的逻辑

上面的代码表明我们有来自$x\_1\_?$到$x\_4\_?$一共4个扭转。每个扭转有四个可选的旋转角度，从$0^o$到$270^o$。例如$x\_3\_2$表示扭转3旋转$90^o$，$x\_4\_2$表示扭转4旋转$0^o$。


以下代码展示了如何引入约束：

![Constraint](../../images/constraint.png)

图 9: 约束的逻辑

模型有时会产生意想不到的结果，例如，$x\_1\_1$、$x\_1\_2$、$x\_1\_3$
和 $x\_1\_4$属于同一个扭转。理论上，模型只能选择其中一个变量。如果模型选择其中的多个，我们必须为其添加惩罚项目。如图所示，当模型选择$x\_1\_?$ 的多个变量时，我们给它惩罚项目$600$ （这里是以 $A=300$ 为例）。

下面的方法来递归计算出不同构型的距离:

```
def update_hubo(torsion_group, up_list, ris):
    if len(torsion_group) == 1:
        for d in range(D):
            final_list = up_list + \
                [var[rb_var_map[torsion_group[0]]][str(d+1)]]
            # distance
            final_list_name = []
            if len(final_list) == 1:
                final_list_name = final_list + final_list
            else:
                final_list_name = final_list

            # update temp points and distance
            self._init_mol_file()

            rb_set = self.mol_data.bond_graph.sort_ris_data[str(
                M)][ris]

            distance = update_pts_distance(
                self.atom_pos_data, rb_set, final_list, var_rb_map, theta_option, True, True)

            hubo_distances[tuple(final_list_name)] = -distance
            logging.debug(
                f"final list {final_list} with distance {distance}")
    else:
        for d in range(D):
            final_list = up_list + \
                [var[rb_var_map[torsion_group[0]]][str(d+1)]]
            update_hubo(torsion_group[1:], final_list, ris)

for ris in mol_data.bond_graph.sort_ris_data[str(M)].keys():
    start = time.time()
    logging.debug(f"ris group {ris} ")
    end = time.time()
    torsion_group = ris.split(",")
    if len(torsion_group) == 1:
        # update constraint
        update_constraint(ris, hubo_constraints)
    logging.debug(torsion_group)
    # update hubo terms
    update_hubo(torsion_group, [], ris)
    logging.debug(
        f"elapsed time for torsion group {ris} : {(end-start)/60} min")
```

## 量子退火

量子退火（QA）可以看作是模拟退火（SA）的一种变体。 QA和SA 都是通过启发式技术来解决具有挑战性的组合问题。QA使用量子涨落（quantum fluctuation）而不是热效应来探索组合空间。本实验使用用于访问加拿大公司D-Wave的Amazon Braket API。该退火器是使用超导量子比特实现的。原生地，QUBO可以使用量子退火器解决：

$$ O(x) = \displaystyle\sum\limits_i h_i x_i + \displaystyle\sum_{i>j} J_{i,j} x_i x_j $$

在QUBO形式中，$x_i \in \{0, 1\}$是二进制变量，可以将其视为我们为特定扭转选择的角度。 $h_i$ 和 $J_{i,j}$
当我们使用相应的角度时，可以认为是编码优化任务的值。但是，通常有片段之间不止一个扭转，在任务里将其建模为HUBO问题：

$$ O(x) = \displaystyle\sum\limits_i \alpha_i x_i + \displaystyle\sum_{i,j} \beta_{i,j} x_i x_j + \displaystyle\sum_{i,j,k} \gamma_{i,j,k} x_i x_j x_k + ../... $$


![Two Frag Mul Tor](../../images/two-frag-multiple-torsion.png)

图 10: 拥有多个扭转

通过添加新的辅助二元变量来替换高阶项，可以将HUBO转换为QUBO。
本方案使用D-Wave软件包中的API $make \_ quadratic()$来进行这种转换。

![HUBO QUBO](../../images/hubo-qubo.png)

图 11: 将HUBO转为QUBO

如图所示，HUBO 的一些高阶项，如 $('x\_1\_1','x\_2\_1','x\_3\_1')$
在 QUBO 中转换为二次项。

