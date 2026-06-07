# Notas de trabajo — Estado del arte (no se incluye en el PDF)

Este directorio (`_notes/`) está ignorado por la compilación de la
memoria (los `\input{}` del `main.tex` no lo tocan). Son notas de
referencia para redactar los capítulos.

Material recopilado el **2026-06-07** por dos búsquedas en paralelo
para preparar el capítulo 2 (Estado del arte). El material está
contrastado contra documentación oficial y venues académicos
primarios; los DOIs y URLs son verificables.

---

## Parte A — Análisis de sistemas comparables (productos)

Análisis crítico de las tres tesis preliminares que el autor llevaba
sobre UnivOrch:

1. ✅ **Combinación "árbol + herencia + closure léxico" sobre VMs** — sí
   es novedosa. Existe scoping léxico en lenguajes de configuración
   (Jsonnet, CUE, Dhall), pero no integrado con modelo organizativo
   jerárquico ni con un orquestador real de VMs.
2. ❌ **Multi-hipervisor agnóstico** — no es novedoso por sí solo. Lo
   hacen libvirt, Vagrant providers, OpenNebula, CloudStack desde
   hace más de diez años.
3. ⚠️ **Delegación a usuarios sin conocimientos** — no es novedad
   técnica (OpenNebula Cloud View, vCloud Tenant Portal, Nutanix
   Self-Service, Kasm Workspaces lo hacen). La novedad real es la
   **metáfora "mesa/ordenador"**, que es contribución de UX, no de
   ingeniería. Defenderla en esos términos.

**Aviso fuerte:** **Crossplane** (Kubernetes) resuelve elegantemente
el desacoplamiento motor / dominio (XRDs + Compositions). UnivOrch
no puede ignorarlo: hay que diferenciarse explícitamente (ventaja
ligereza sin clúster Kubernetes; limitación: Crossplane es más
maduro y más extensible).

### Tabla comparativa (15 sistemas)

| Sistema | Tipo | Multi-hipervisor | Jerarquía | Herencia propiedades | Closure léxico | Delegación a usuarios finales | Motor / dominio | GitOps VMs |
|---|---|---|---|---|---|---|---|---|
| OpenNebula | OSS cloud privado | Sí (KVM, LXC, vSphere, Firecracker) | Grupos / VDCs (2 niveles) | Parcial | No | Sí (Sunstone Cloud View) | No | No |
| Apache CloudStack | OSS cloud privado | Sí (KVM, vSphere, XenServer, Hyper-V) | Region > Zone > Pod > Cluster + Domain > Account | Cuotas heredan; templates planos | No | Sí (User Portal) | No | No |
| oVirt | OSS | No (solo KVM/RHV) | Data Center > Cluster > Host | Sí: VM hereda machine-type/CPU del cluster | No | Limitada | No | Externa |
| Proxmox VE | OSS | No (KVM + LXC) | Pools anidados (PVE 8.1) | Permisos sí; props VM no | No | No | No | Vía Terraform |
| VMware vCloud Director | Comercial | Limitada (vSphere/NSX) | Provider VDC > Org > Org VDC > vApp | Catálogos compartibles | No | Sí (Tenant Portal) | Parcial multi-tenant | Vía Terraform |
| Proxmox DCM | Comercial (beta) | No | Multi-cluster | Limitada | No | No | No | No |
| Nutanix Prism / Self-Service | Comercial | Limitada (AHV, ESXi) | Proyectos, categorías | Categorías como etiquetas | No | Sí (marketplace) | Parcial | Calm blueprints |
| GNS3 / EVE-NG / CML | Lab de redes | Parcial | Proyecto plano | No | No | No (usuario técnico) | No | No |
| Labtainers | Lab docente cibersec | No (Docker) | Plano | Parametrización por estudiante | No | Sí (estudiante) | Sí (framework + labs) | No |
| Kasm Workspaces | DaaS / lab efímero | No | Workspaces, grupos | Plantilla de workspace | No | Sí (web) | Parcial | No |
| Vagrant | Declarativo VM dev | Sí (VirtualBox, VMware, libvirt, Hyper-V) | Plano (Vagrantfile) | Sí dentro de un fichero | No | No | Sí (provider plugins) | No |
| Terraform + providers VM | Declarativo IaC | Sí (módulos) | Modules > resources | Variables no heredan auto | No (variables aisladas por módulo) | No | Sí | Sí (Atlantis, TF Cloud) |
| Kubernetes + HNC + KubeVirt | Declarativo orquestación | KubeVirt solo KVM | Hierarchical Namespaces (árbol N niveles) | Sí: RBAC, ResourceQuota, NetworkPolicy propagan | No | No (kubectl) | Sí (k8s + operadores) | Sí (ArgoCD / Flux) |
| Crossplane | Declarativo platform API | Sí (cualquier provider) | XRD/Composition (composición, no árbol) | Composiciones encadenables | No | Sí (Claims como API simplificada) | Sí (XRD = abstracción de dominio) | Sí |
| Jsonnet / CUE / Dhall | Lenguaje de configuración | N/A | N/A | Sí (super/self, unificación CUE) | Sí (Jsonnet) | No | N/A | N/A |

### Referencias técnicas (documentación oficial)

1. OpenNebula Systems, 2026 — *OpenNebula 6.10 Documentation: Users, Groups and Resource Management* — https://docs.opennebula.io/6.10/management_and_operations/users_groups_management/
2. The Apache Software Foundation, 2026 — *Apache CloudStack 4.22 Administration Guide: Roles, Accounts, Users, and Domains* — https://docs.cloudstack.apache.org/en/latest/adminguide/accounts.html
3. Proxmox Server Solutions GmbH, 2026 — *Proxmox VE Administration Guide: User Management and Pools* — https://pve.proxmox.com/wiki/User_Management
4. VMware (Broadcom), 2024 — *VMware Cloud Director 10.6 Service Provider Admin Guide* — https://docs.vmware.com/en/VMware-Cloud-Director/
5. Kubernetes SIG-Multitenancy, 2020 — *Introducing Hierarchical Namespaces (HNC)* — https://kubernetes.io/blog/2020/08/14/introducing-hierarchical-namespaces/
6. Red Hat, 2024 — *Virtual Machines as Code with OpenShift GitOps and OpenShift Virtualization* — https://www.redhat.com/en/blog/virtual-machines-as-code-with-openshift-gitops-and-openshift-virtualization (y https://kubevirt.io/user-guide/cluster_admin/gitops/)
7. Crossplane Authors / Upbound, 2024 — *Crossplane Documentation: Composite Resource Definitions and Compositions* — https://docs.crossplane.io/latest/concepts/composite-resource-definitions/
8. C. Irvine, M. Thompson et al., 2017 — *Labtainers: A Docker-based Framework for Cybersecurity Labs* — USENIX ASE'17 — https://www.usenix.org/system/files/conference/ase17/ase17_paper_irvine.pdf
9. Google, 2020 — *Jsonnet Language Reference: Lexical Scoping and Object Inheritance* — https://jsonnet.org/ref/language.html
10. oVirt Project, 2024 — *oVirt Administration Guide: Data Centers, Clusters and Templates* — https://www.ovirt.org/documentation/administration_guide/

---

## Parte B — Referencias académicas (papers, libros, estándares)

### Tema 1 — Virtualización y orquestación en docencia universitaria

**Pieza clave — antecedente directo de UnivOrch:**

- **Vouk, M. A., Averritt, S., Bugaev, M., Kurth, A., Peeler, A.,
  Schaffer, H., Sills, E., Stein, S., Thompson, J.** (2009). *"NCSU's
  Virtual Computing Lab: A Cloud Computing Solution"*. **IEEE
  Computer 42(7): 94–97.** DOI: 10.1109/MC.2009.230.
  El VCL de North Carolina State es el antecedente académico más
  cercano. Open source, pensado explícitamente para docencia e
  investigación, sirve 40.000 usuarios. **Comparación honesta:** VCL
  es monolítico y muy ligado a su infraestructura concreta; UnivOrch
  es agnóstico de hipervisor, declarativo, y la capa-2 se puede
  desacoplar y reescribir para otros dominios. **Merece una
  subsección propia en el cap. 2.**

- **Vouk, M. A.** (2008). *"Cloud Computing — Issues, Research and
  Implementations"*. Journal of Computing and Information Technology
  16(4): 235–246. URL: http://cit.fer.hr/index.php/CIT/article/view/1674

- **Averitt, S. et al.** (2007). *"The Virtual Computing Laboratory"*.
  Proc. International Conference on Virtual Computing Initiative, IBM
  Corp. URL: https://vcl.ncsu.edu/

### Tema 2 — Modelos declarativos para infraestructura

- **Rahman, A., Mahdavi-Hezaveh, R., Williams, L.** (2019). *"A
  systematic mapping study of infrastructure as code research"*.
  Information and Software Technology 108: 65–77.
  DOI: 10.1016/j.infsof.2018.12.004.

- **Rahman, A., Williams, L.** (2019). *"Source code properties of
  defective infrastructure as code scripts"*. Information and
  Software Technology 112: 148–163. DOI: 10.1016/j.infsof.2019.04.013.

- **Burgess, M.** (2003). *"On the theory of system administration"*.
  Science of Computer Programming 49(1–3): 1–46.
  DOI: 10.1016/j.scico.2003.08.001.
  Fundacional. Convergencia (estado deseado vs. real) sustenta
  Terraform, Ansible y el modelo declarativo de UnivOrch.

### Tema 3 — Capas de abstracción sobre hipervisores

- **Bolte, M., Sievers, M., Birkenheuer, G., Niehörster, O.,
  Brinkmann, A.** (2010). *"Non-intrusive virtualization management
  using libvirt"*. Proc. DATE 2010, IEEE: 574–579.
  DOI: 10.1109/DATE.2010.5457142.
  **Cita obligada.** Precedente directo del diseño de
  `HypervisorConnector` (ABC) de UnivOrch.

- **DMTF DSP0243** — *Open Virtualization Format (OVF) Specification*
  — https://www.dmtf.org/standards/ovf
  Citar el estándar directamente para portabilidad de VMs entre
  hipervisores; mejor que un paper débil.

### Tema 4 — RBAC y delegación

- **Sandhu, R. S., Coyne, E. J., Feinstein, H. L., Youman, C. E.**
  (1996). *"Role-Based Access Control Models"*. IEEE Computer
  29(2): 38–47. DOI: 10.1109/2.485845.
  **Cita canónica del RBAC**, incluye el modelo RBAC1 con jerarquía
  de roles (herencia), que es el modelo conceptual que UnivOrch
  implementa siguiendo el árbol de carpetas.

- **Ferraiolo, D. F., Sandhu, R., Gavrila, S., Kuhn, D. R.,
  Chandramouli, R.** (2001). *"Proposed NIST standard for role-based
  access control"*. ACM Transactions on Information and System
  Security 4(3): 224–274. DOI: 10.1145/501978.501980.

- **ANSI INCITS 359-2004** — *Role-Based Access Control*. American
  National Standards Institute, 2004. Estándar formal.

### Tema 5 — Closure léxico (analogía conceptual)

- **Sussman, G. J., Steele, G. L.** (1975). *"Scheme: An Interpreter
  for Extended Lambda Calculus"*. MIT AI Memo 349.
  URL: https://dspace.mit.edu/handle/1721.1/5794
  Paper original que introduce scoping léxico en Lisp. Cita de
  pedigrí.

- **Abelson, H., Sussman, G. J., Sussman, J.** (1996). *Structure
  and Interpretation of Computer Programs*, 2nd ed. MIT Press.
  ISBN 0-262-01153-0.
  Capítulo 3 trata entornos y closures con la elegancia adecuada
  para la analogía. **No exagerar esta sección**: una nota a pie de
  página o un párrafo basta para introducir la idea aplicada a
  infraestructura.

### Tema 6 — VMs vs contenedores en docencia

- **Vykopal, J., Ošlejšek, R., Čeleda, P., Vizváry, M., Tovarňák, D.**
  (2017). *"KYPO Cyber Range: Design and Use Cases"*. Proc. ICSOFT
  2017. DOI: 10.5220/0006428203100321.
  Argumenta por qué la ciberseguridad práctica exige VMs reales
  (kernel privilegiado, redes complejas), no contenedores.

- **Beuran, R., Tang, D., Pham, C., Chinen, K., Tan, Y., Shinoda, Y.**
  (2018). *"Integrated framework for hands-on cybersecurity training:
  CyTrONE"*. Computers & Security 78: 43–59.
  DOI: 10.1016/j.cose.2018.06.001.
  Compara explícitamente VMs vs. Docker para entornos de entrenamiento.

- **Willems, C., Meinel, C.** (2012). *"Online assessment for hands-on
  cyber security training in a virtual lab"*. Proc. IEEE Global
  Engineering Education Conference (EDUCON).
  DOI: 10.1109/EDUCON.2012.6201149.
  Tele-Lab (HPI Potsdam). Referencia clásica de laboratorio virtual
  basado en VMs para enseñanza de seguridad.

### Tema 7 — Trabajos previos del tutor

**Resultado honesto:** Guillermo Pérez Trabado (UMA, Dpto.
Arquitectura de Computadores) no tiene publicaciones académicas
sobre orquestación de VMs, `esxobjects` ni `yamlinfr`. Sus líneas
indexadas son bioinformática, HPC, posicionamiento indoor, OBD,
smart cities.

- Perfil UMA: https://www.uma.es/departments/teachers/N09xY2RCVkFwTGlDcmJyb3dQb0tQZz09/
- Página personal: https://www.ac.uma.es/~guille/
- Google Scholar: https://scholar.google.com/citations?user=G2X2cxMAAAAJ
- ResearchGate: https://www.researchgate.net/profile/Guillermo-Trabado

Es responsable técnico del **Laboratorio de Supercomputación de la
UMA** — eso da contexto institucional al TFG (experiencia en
infraestructuras). Las librerías `esxobjects` y `yamlinfr` parecen
software interno docente no publicado. **Recomendación:** citarlas
como *"trabajo previo no publicado del tutor"* o como comunicación
personal. **No inflar** con publicaciones suyas no relacionadas.

---

## Estructura propuesta para el capítulo 2

```
2. State of the art
  2.1 The teaching virtualization landscape     ← VCL como antecedente principal
  2.2 Multi-hypervisor abstraction layers        ← libvirt, OpenNebula, CloudStack
  2.3 Declarative infrastructure management      ← Burgess, Rahman, Terraform, Crossplane
  2.4 Hierarchical RBAC and tenant delegation    ← Sandhu, Kubernetes HNC, vCloud
  2.5 Lexical scoping applied to infrastructure  ← Jsonnet/CUE, SICP (analogía)
  2.6 Container-based vs VM-based educational labs ← KYPO, CyTrONE, Labtainers
  2.7 Positioning of UnivOrch                    ← qué hueco ocupa y qué no
```

## Próximo paso al redactar

1. Cargar las referencias en `docs/memoria/references.bib`.
2. Redactar capítulo 2 con esta estructura, **sin inflar la novedad**.
3. Comparativa explícita con VCL (Vouk 2009), Crossplane (la cita
   que duele) y libvirt (la honestidad sobre el ABC).
