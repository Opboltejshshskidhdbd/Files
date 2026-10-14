// Luau validator v3: lexer + parser + scope analysis + pass-2 type/API analysis (NOT the official Luau compiler).
// Works in browsers (ES module), Cloudflare Workers and Node.
const KW=new Set("and break do else elseif end false for function if in local nil not or repeat return then true until while".split(" "));
const GLOBALS=new Set("assert error getmetatable setmetatable ipairs pairs next pcall xpcall select tonumber tostring type typeof print warn rawequal rawget rawset rawlen require unpack newproxy collectgarbage gcinfo tick time wait spawn delay elapsedTime loadstring getfenv setfenv os math string table coroutine utf8 bit32 debug buffer task game workspace Workspace script plugin shared settings stats UserSettings version _G _VERSION Enum Instance Vector2 Vector3 Vector2int16 Vector3int16 Region3 Region3int16 CFrame Color3 BrickColor UDim UDim2 Rect Ray TweenInfo NumberRange NumberSequence NumberSequenceKeypoint ColorSequence ColorSequenceKeypoint Random DateTime Axes Faces Font OverlapParams RaycastParams PathWaypoint PhysicalProperties CatalogSearchParams DockWidgetPluginGuiInfo SharedTable FloatCurveKey RotationCurveKey".split(" "));
const SERVICES=new Set("Workspace Players Lighting ReplicatedStorage ReplicatedFirst ServerStorage ServerScriptService StarterGui StarterPack StarterPlayer Teams SoundService Chat TextChatService RunService UserInputService ContextActionService TweenService HttpService MarketplaceService DataStoreService MessagingService TeleportService CollectionService PhysicsService PathfindingService Debris GuiService TextService BadgeService GroupService LocalizationService VRService ProximityPromptService MemoryStoreService ContentProvider HapticService SocialService PolicyService AnalyticsService Stats InsertService AssetService CoreGui ScriptContext TestService KeyframeSequenceProvider AvatarEditorService Selection StudioService NetworkClient NetworkServer LogService VirtualInputManager RbxAnalyticsService MaterialService TouchInputService VoiceChatService UserService ExperienceService OpenCloudService Players DataStoreService LocalizationService RunService SelectionService ChangeHistoryService ServerScriptService StarterPlayer StarterGui Visit GamePassService NotificationService CaptureService AvatarChatService HttpRbxApiService ScriptService ReflectionService UGCValidationService AdService CookiesService".split(" "));
const CLASSES=new Set("Part MeshPart WedgePart CornerWedgePart TrussPart SpawnLocation Model Folder Tool Accessory Humanoid Script LocalScript ModuleScript RemoteEvent RemoteFunction BindableEvent BindableFunction StringValue IntValue NumberValue BoolValue ObjectValue Vector3Value CFrameValue Color3Value BrickColorValue Attachment Weld WeldConstraint Motor6D HingeConstraint SpringConstraint RopeConstraint AlignPosition AlignOrientation LinearVelocity AngularVelocity BodyVelocity BodyGyro BodyPosition BodyForce Sound SoundGroup ParticleEmitter Beam Trail Fire Smoke Sparkles Explosion PointLight SpotLight SurfaceLight Highlight Decal Texture SurfaceGui ScreenGui BillboardGui Frame TextLabel TextButton TextBox ImageLabel ImageButton ScrollingFrame ViewportFrame UICorner UIStroke UIListLayout UIGridLayout UIPadding UIScale UIGradient UIAspectRatioConstraint Animation Animator AnimationController Camera ClickDetector ProximityPrompt Seat VehicleSeat Configuration Shirt Pants ShirtGraphic ForceField Team Atmosphere Sky BlurEffect ColorCorrectionEffect BloomEffect SunRaysEffect DepthOfFieldEffect".split(" "));
const YIELD=new Set(["wait","Wait","WaitForChild","sleep"]);
const COMP=new Set(["+=","-=","*=","/=","//=","%=","^=","..="]);
const BIN={or:[1,1],and:[2,2],"<":[3,3],">":[3,3],"<=":[3,3],">=":[3,3],"~=":[3,3],"==":[3,3],"..":[5,4],"+":[6,6],"-":[6,6],"*":[7,7],"/":[7,7],"//":[7,7],"%":[7,7],"^":[10,9]};

function lex(s){
  const T=[],E=[],n=s.length,out=[];let i=0,line=1,ls=0;
  const blank=(a,b)=>{for(let k=a;k<b;k++){if(s[k]==="\n"){line++;ls=k+1;out.push("\n")}else out.push(" ")}};
  const long=p=>{const m=/^\[(=*)\[/.exec(s.slice(p,p+50));if(!m)return -1;const c="]"+m[1]+"]",e=s.indexOf(c,p+m[0].length);return e<0?-2:e+c.length};
  const two=new Set(["==","~=","<=",">=","..","//","+=","-=","*=","/=","%=","^=","::","->"]);
  while(i<n){
    const ch=s[i],col=i-ls+1,ln=line;
    if(ch==="\n"){line++;ls=i+1;out.push(ch);i++;continue}
    if(/\s/.test(ch)){out.push(ch);i++;continue}
    if(ch==="-"&&s[i+1]==="-"){
      let e=long(i+2);
      if(e===-2){E.push({line:ln,col,rule:"syntax",severity:"error",message:"Unclosed long comment"});e=n}
      else if(e<0){e=s.indexOf("\n",i);if(e<0)e=n}
      blank(i,e);i=e;continue}
    if(ch==='"'||ch==="'"||ch==="`"){
      let k=i+1,ok=false;
      while(k<n){const d=s[k];if(d==="\\"){k+=2;continue}if(d===ch){ok=true;break}if(d==="\n"&&ch!=="`")break;k++}
      if(!ok)E.push({line:ln,col,rule:"syntax",severity:"error",message:"Unclosed string"});
      const e=ok?k+1:Math.min(k,n);
      T.push({t:"str",v:s.slice(i+1,ok?e-1:e),raw:s.slice(i,e),line:ln,col});blank(i,e);i=e;continue}
    if(ch==="["){
      const e=long(i);
      if(e===-2){E.push({line:ln,col,rule:"syntax",severity:"error",message:"Unclosed long string"});blank(i,n);i=n;continue}
      if(e>0){T.push({t:"str",v:"",raw:"[[",line:ln,col});blank(i,e);i=e;continue}}
    if(/\d/.test(ch)||(ch==="."&&/\d/.test(s[i+1]||""))){
      const m=/^(0[xX][\da-fA-F_]+|0[bB][01_]+|(?:\d[\d_]*\.(?!\.)[\d_]*|\.\d[\d_]*|\d[\d_]*)(?:[eE][+-]?\d+)?)/.exec(s.slice(i,i+60));
      const v=m?m[0]:ch;T.push({t:"num",v,line:ln,col});out.push(v);i+=v.length;continue}
    if(/[A-Za-z_]/.test(ch)){
      const v=/^\w+/.exec(s.slice(i,i+200))[0];
      T.push({t:KW.has(v)?"kw":"id",v,line:ln,col});out.push(v);i+=v.length;continue}
    let v=ch;
    const t3=s.substr(i,3);
    if(t3==="..."||t3==="..="||t3==="//=")v=t3;else if(two.has(s.substr(i,2)))v=s.substr(i,2);
    if(v.length===1&&"$!\\".includes(v))E.push({line:ln,col,rule:"syntax",severity:"error",message:`Unexpected character '${v}'`});
    T.push({t:"sym",v,line:ln,col});out.push(v);i+=v.length;
  }
  T.push({t:"eof",v:"<eof>",line,col:i-ls+1});
  return{T,E,clean:out.join("")};
}


// ===== Roblox API database (partial; classes flagged F have complete member lists) =====
// Format per line: Class|Parent|flags|member;member;...   member: Prop:Type | Method(P1,P2?,...Rest):Ret | Event@(T1,T2)
// <<API_DB_START>>
const API_SRC=`
Instance||F|Name:string;Parent:Instance?;ClassName:string;Archivable:boolean;Capabilities:any;RobloxLocked:boolean;Sandboxed:boolean;UniqueId:any;SourceAssetId:number;HistoryId:any;AddTag(string);ClearAllChildren();Clone():Instance;Destroy();FindFirstAncestor(string):Instance?;FindFirstAncestorOfClass(string):Instance?;FindFirstAncestorWhichIsA(string):Instance?;FindFirstChild(string,boolean?):Instance?;FindFirstChildOfClass(string):Instance?;FindFirstChildWhichIsA(string,boolean?):Instance?;FindFirstDescendant(string):Instance?;GetActor():Instance?;GetAttribute(string):any;GetAttributeChangedSignal(string):any;GetAttributes():any;GetChildren():{Instance};GetDebugId(number?):string;GetDescendants():{Instance};GetFullName():string;GetPropertyChangedSignal(string):any;GetStyled(string):any;GetTags():{string};HasTag(string):boolean;IsA(string):boolean;IsAncestorOf(Instance):boolean;IsDescendantOf(Instance):boolean;IsPropertyModified(string):boolean;RemoveTag(string);ResetPropertyToDefault(string);SetAttribute(string,any);WaitForChild(string,number?):Instance;Remove();AncestryChanged@(Instance,Instance?);AttributeChanged@(string);Changed@(any);ChildAdded@(Instance);ChildRemoved@(Instance);DescendantAdded@(Instance);DescendantRemoving@(Instance);Destroying@();StyledPropertiesChanged@()
PVInstance|Instance|F|GetPivot():CFrame;PivotTo(CFrame)
BasePart|PVInstance|F|Anchored:boolean;AssemblyAngularVelocity:Vector3;AssemblyCenterOfMass:Vector3;AssemblyLinearVelocity:Vector3;AssemblyMass:number;AssemblyRootPart:BasePart;AudioCanCollide:boolean;BackSurface:Enum.SurfaceType;BottomSurface:Enum.SurfaceType;BrickColor:BrickColor;CFrame:CFrame;CanCollide:boolean;CanQuery:boolean;CanTouch:boolean;CastShadow:boolean;CenterOfMass:Vector3;CollisionGroup:string;CollisionGroupId:number;Color:Color3;CurrentPhysicalProperties:PhysicalProperties;CustomPhysicalProperties:PhysicalProperties?;EnableFluidForces:boolean;ExtentsCFrame:CFrame;ExtentsSize:Vector3;FrontSurface:Enum.SurfaceType;LeftSurface:Enum.SurfaceType;RightSurface:Enum.SurfaceType;TopSurface:Enum.SurfaceType;BackSurfaceInput:Enum.InputType;BottomSurfaceInput:Enum.InputType;FrontSurfaceInput:Enum.InputType;LeftSurfaceInput:Enum.InputType;RightSurfaceInput:Enum.InputType;TopSurfaceInput:Enum.InputType;LocalTransparencyModifier:number;Locked:boolean;Mass:number;Massless:boolean;Material:Enum.Material;MaterialVariant:string;Orientation:Vector3;PivotOffset:CFrame;Position:Vector3;Reflectance:number;ResizeIncrement:number;ResizeableFaces:Faces;RootPriority:number;Rotation:Vector3;Size:Vector3;Transparency:number;Velocity:Vector3;RotVelocity:Vector3;ApplyAngularImpulse(Vector3);ApplyImpulse(Vector3);ApplyImpulseAtPosition(Vector3,Vector3);BreakJoints();CanCollideWith(BasePart):boolean;CanSetNetworkOwnership():any;GetClosestPointOnSurface(Vector3):Vector3;GetConnectedParts(boolean?):{BasePart};GetJoints():{Instance};GetMass():number;GetNetworkOwner():Player?;GetNetworkOwnershipAuto():boolean;GetNoCollisionConstraints():{Instance};GetRootPart():BasePart;GetTouchingParts():{BasePart};GetVelocityAtPosition(Vector3):Vector3;IntersectAsync({BasePart},any?,any?):any;IsGrounded():boolean;MakeJoints();Resize(Enum.NormalId,number):boolean;SetNetworkOwner(Player?);SetNetworkOwnershipAuto();SubtractAsync({BasePart},any?,any?):any;UnionAsync({BasePart},any?,any?):any;Touched@(BasePart);TouchEnded@(BasePart)
Part|BasePart|F|Shape:Enum.PartType;FormFactor:any
WedgePart|BasePart|F|
CornerWedgePart|BasePart|F|
TrussPart|BasePart|F|Style:any
SpawnLocation|Part||AllowTeamChangeOnTouch:boolean;Duration:number;Enabled:boolean;Neutral:boolean;TeamColor:BrickColor
Seat|Part||Disabled:boolean;Occupant:Humanoid?;Sit(Humanoid)
VehicleSeat|BasePart||Throttle:number;Steer:number;MaxSpeed:number;Torque:number;TurnSpeed:number;Occupant:Humanoid?
MeshPart|BasePart||MeshId:string;TextureID:string;MeshSize:Vector3;CollisionFidelity:Enum.CollisionFidelity;RenderFidelity:Enum.RenderFidelity;DoubleSided:boolean
UnionOperation|BasePart||UsePartColor:boolean;CollisionFidelity:Enum.CollisionFidelity;RenderFidelity:Enum.RenderFidelity
Model|PVInstance||LevelOfDetail:any;ModelStreamingMode:any;PrimaryPart:BasePart?;WorldPivot:CFrame;AddPersistentPlayer(Player?);BreakJoints();GetBoundingBox():CFrame;GetExtentsSize():Vector3;GetPersistentPlayers():{Player};GetScale():number;MakeJoints();MoveTo(Vector3);RemovePersistentPlayer(Player?);ScaleTo(number);SetPrimaryPartCFrame(CFrame);TranslateBy(Vector3)
WorldRoot|Model||Raycast(Vector3,Vector3,RaycastParams?):RaycastResult?;GetPartBoundsInBox(CFrame,Vector3,OverlapParams?):{BasePart};GetPartBoundsInRadius(Vector3,number,OverlapParams?):{BasePart};GetPartsInPart(BasePart,OverlapParams?):{BasePart}
Workspace|WorldRoot||CurrentCamera:Camera?;Gravity:number;FallenPartsDestroyHeight:number;Terrain:any;DistributedGameTime:number;StreamingEnabled:boolean;GetServerTimeNow():number
Folder|Instance|F|
Configuration|Instance|F|
Actor|Model||
Accessory|Instance||AccessoryType:any;Handle:any
Tool|Instance||CanBeDropped:boolean;Enabled:boolean;Grip:CFrame;GripForward:Vector3;GripPos:Vector3;GripRight:Vector3;GripUp:Vector3;ManualActivationOnly:boolean;RequiresHandle:boolean;ToolTip:string;Activate();Deactivate();Activated@();Deactivated@();Equipped@(any);Unequipped@()
Humanoid|Instance||Health:number;MaxHealth:number;WalkSpeed:number;JumpPower:number;JumpHeight:number;HipHeight:number;DisplayName:string;DisplayDistanceType:any;HealthDisplayType:any;RigType:Enum.HumanoidRigType;FloorMaterial:Enum.Material;MoveDirection:Vector3;Sit:boolean;Jump:boolean;PlatformStand:boolean;AutoRotate:boolean;AutoJumpEnabled:boolean;UseJumpPower:boolean;CameraOffset:Vector3;RootPart:BasePart?;SeatPart:Seat?;WalkToPart:BasePart?;WalkToPoint:Vector3;TakeDamage(number);MoveTo(Vector3,BasePart?);Move(Vector3,boolean?);ChangeState(any);GetState():any;EquipTool(Tool);UnequipTools();AddAccessory(Accessory);RemoveAccessories();GetAccessories():{Accessory};GetPlayingAnimationTracks():any;LoadAnimation(Animation):any;Died@();HealthChanged@(number);Running@(number);Jumping@(boolean);Seated@(boolean,Seat);StateChanged@(any,any);Touched@(BasePart,BasePart);FreeFalling@(boolean);Climbing@(number);Swimming@(number);GettingUp@(boolean);FallingDown@(boolean);PlatformStanding@(boolean);Strafing@(boolean);MoveToFinished@(boolean)
Animator|Instance||LoadAnimation(Animation):any;GetPlayingAnimationTracks():any;AnimationPlayed@(any)
Animation|Instance||AnimationId:string
Sound|Instance||SoundId:string;Volume:number;Playing:boolean;Looped:boolean;PlaybackSpeed:number;TimePosition:number;TimeLength:number;IsPlaying:boolean;IsLoaded:boolean;RollOffMode:any;RollOffMaxDistance:number;RollOffMinDistance:number;SoundGroup:any;Play();Stop();Pause();Resume();Played@(number);Paused@(number);Resumed@(number);Stopped@(number);Ended@(number);Loaded@(number);DidLoop@(string,number)
Attachment|Instance||CFrame:CFrame;Position:Vector3;Orientation:Vector3;Rotation:Vector3;WorldCFrame:CFrame;WorldPosition:Vector3;WorldOrientation:Vector3;WorldRotation:Vector3;WorldAxis:Vector3;WorldSecondaryAxis:Vector3;Axis:Vector3;SecondaryAxis:Vector3;Visible:boolean
WeldConstraint|Instance||Part0:BasePart?;Part1:BasePart?;Enabled:boolean;Active:boolean
ProximityPrompt|Instance||ActionText:string;ObjectText:string;HoldDuration:number;MaxActivationDistance:number;Enabled:boolean;KeyboardKeyCode:Enum.KeyCode;GamepadKeyCode:Enum.KeyCode;RequiresLineOfSight:boolean;ClickablePrompt:boolean;Exclusivity:any;Style:any;UIOffset:Vector2;RootPrompt:any;InputHoldBegin();InputHoldEnd();Triggered@(Player);TriggerEnded@(Player);PromptShown@();PromptHidden@();PromptButtonHoldBegan@(Player);PromptButtonHoldEnded@(Player)
Camera|Instance||CFrame:CFrame;CameraType:Enum.CameraType;CameraSubject:Instance?;FieldOfView:number;Focus:CFrame;ViewportSize:Vector2;ScreenPointToRay(number,number,number?):Ray;ViewportPointToRay(number,number,number?):Ray;WorldToScreenPoint(Vector3):Vector3;WorldToViewportPoint(Vector3):Vector3
ValueBase|Instance||
StringValue|ValueBase|F|Value:string
IntValue|ValueBase|F|Value:number
NumberValue|ValueBase|F|Value:number
BoolValue|ValueBase|F|Value:boolean
ObjectValue|ValueBase|F|Value:Instance?
Vector3Value|ValueBase|F|Value:Vector3
CFrameValue|ValueBase|F|Value:CFrame
Color3Value|ValueBase|F|Value:Color3
BrickColorValue|ValueBase|F|Value:BrickColor
RemoteEvent|Instance|F|FireServer(...any);FireClient(Player,...any);FireAllClients(...any);OnServerEvent@(Player,...any);OnClientEvent@(...any)
UnreliableRemoteEvent|Instance|F|FireServer(...any);FireClient(Player,...any);FireAllClients(...any);OnServerEvent@(Player,...any);OnClientEvent@(...any)
RemoteFunction|Instance|F|InvokeServer(...any):any;InvokeClient(Player,...any):any;OnServerInvoke:fn;OnClientInvoke:fn
BindableEvent|Instance|F|Fire(...any);Event@(...any)
BindableFunction|Instance|F|Invoke(...any):any;OnInvoke:fn
Player|Instance||UserId:number;DisplayName:string;Character:Model?;CharacterAdded@(Model);CharacterRemoving@(Model);CharacterAppearanceLoaded@(Model);Team:any;TeamColor:BrickColor;Neutral:boolean;AccountAge:number;MembershipType:Enum.MembershipType;CameraMode:any;CanLoadCharacterAppearance:boolean;CharacterAppearanceId:number;FollowUserId:number;LocaleId:string;RespawnLocation:SpawnLocation?;AutoJumpEnabled:boolean;CameraMaxZoomDistance:number;CameraMinZoomDistance:number;Kick(string?);LoadCharacter();GetMouse():any;GetRankInGroup(number):number;GetRoleInGroup(number):string;IsInGroup(number):boolean;IsFriendsWith(number):boolean;GetJoinData():any;HasAppearanceLoaded():boolean;ClearCharacterAppearance();Move(Vector3,boolean?);DistanceFromCharacter(Vector3):number;Chatted@(string,Player?);Idled@(number)
Players|Instance||LocalPlayer:Player;MaxPlayers:number;NumPlayers:number;RespawnTime:number;CharacterAutoLoads:boolean;PlayerAdded@(Player);PlayerRemoving@(Player);GetPlayers():{Player};GetPlayerByUserId(number):Player?;GetPlayerFromCharacter(Instance):Player?;GetUserIdFromNameAsync(string):number;GetNameFromUserIdAsync(number):string;GetHumanoidDescriptionFromUserId(number):any;GetCharacterAppearanceInfoAsync(number):any
RunService|Instance||Heartbeat@(number);RenderStepped@(number);Stepped@(number,number);PreRender@(number);PreAnimation@(number);PreSimulation@(number);PostSimulation@(number);IsClient():boolean;IsServer():boolean;IsStudio():boolean;IsRunning():boolean;IsEdit():boolean;IsRunMode():boolean;BindToRenderStep(string,number,fn);UnbindFromRenderStep(string)
TweenService|Instance||Create(Instance,TweenInfo,any):Tween;GetValue(number,Enum.EasingStyle,Enum.EasingDirection):number
Tween|Instance||PlaybackState:Enum.PlaybackState;Instance:Instance;TweenInfo:TweenInfo;Play();Pause();Cancel();Completed@(Enum.PlaybackState)
HttpService|Instance||HttpEnabled:boolean;JSONEncode(any):string;JSONDecode(string):any;GenerateGUID(boolean?):string;GetAsync(string,boolean?,any?):string;PostAsync(string,string,any?,boolean?,any?):string;RequestAsync(any):any;UrlEncode(string):string
DataStoreService|Instance||GetDataStore(string,string?,any?):DataStore;GetOrderedDataStore(string,string?):DataStore;GetGlobalDataStore():DataStore;ListDataStoresAsync(string?,number?,string?):any;GetRequestBudgetForRequestType(any):number
DataStore|Instance||GetAsync(string,any?):any;SetAsync(string,any,{number}?,any?):string;UpdateAsync(string,fn):any;RemoveAsync(string):any;IncrementAsync(string,number?,{number}?,any?):number;ListKeysAsync(string?,number?,string?,boolean?):any;GetVersionAsync(string,string):any
ReplicatedStorage|Instance||
ServerStorage|Instance||
ServerScriptService|Instance||
Lighting|Instance||Brightness:number;ClockTime:number;TimeOfDay:string;Ambient:Color3;OutdoorAmbient:Color3;FogEnd:number;FogStart:number;FogColor:Color3;GlobalShadows:boolean;ExposureCompensation:number;GetMinutesAfterMidnight():number;SetMinutesAfterMidnight(number)
UserInputService|Instance||MouseEnabled:boolean;KeyboardEnabled:boolean;TouchEnabled:boolean;GamepadEnabled:boolean;MouseBehavior:Enum.MouseBehavior;MouseIconEnabled:boolean;InputBegan@(any,boolean);InputEnded@(any,boolean);InputChanged@(any,boolean);GetMouseLocation():Vector2;IsKeyDown(Enum.KeyCode):boolean;IsMouseButtonPressed(Enum.UserInputType):boolean;GetKeysPressed():any
RBXScriptConnection||F|Connected:boolean;Disconnect()
GuiBase2d|Instance||AbsolutePosition:Vector2;AbsoluteSize:Vector2;AbsoluteRotation:number
GuiObject|GuiBase2d||Active:boolean;AnchorPoint:Vector2;AutomaticSize:Enum.AutomaticSize;BackgroundColor3:Color3;BackgroundTransparency:number;BorderColor3:Color3;BorderSizePixel:number;ClipsDescendants:boolean;LayoutOrder:number;Position:UDim2;Rotation:number;Size:UDim2;SizeConstraint:Enum.SizeConstraint;Visible:boolean;ZIndex:number;Selectable:boolean;InputBegan@(any);InputEnded@(any);InputChanged@(any);MouseEnter@(number,number);MouseLeave@(number,number);MouseMoved@(number,number);TweenPosition(UDim2,any?,any?,number?,boolean?,fn?):boolean;TweenSize(UDim2,any?,any?,number?,boolean?,fn?):boolean;TweenSizeAndPosition(UDim2,UDim2,any?,any?,number?,boolean?,fn?):boolean
Frame|GuiObject||Style:any
ScrollingFrame|GuiObject||CanvasSize:UDim2;CanvasPosition:Vector2;ScrollBarThickness:number;ScrollingEnabled:boolean
TextLabel|GuiObject||Text:string;TextColor3:Color3;TextSize:number;TextScaled:boolean;TextWrapped:boolean;Font:Enum.Font;FontFace:any;RichText:boolean;TextTransparency:number;TextXAlignment:Enum.TextXAlignment;TextYAlignment:Enum.TextYAlignment;TextStrokeTransparency:number;TextStrokeColor3:Color3;LineHeight:number;MaxVisibleGraphemes:number;TextBounds:Vector2;TextFits:boolean;TextTruncate:any;TextDirection:any;LocalizedText:string;ContentText:string;OpenTypeFeatures:string
TextButton|GuiObject||Text:string;TextColor3:Color3;TextSize:number;TextScaled:boolean;TextWrapped:boolean;Font:Enum.Font;FontFace:any;RichText:boolean;TextTransparency:number;TextXAlignment:Enum.TextXAlignment;TextYAlignment:Enum.TextYAlignment;TextStrokeTransparency:number;TextStrokeColor3:Color3;AutoButtonColor:boolean;Modal:boolean;Style:any;Activated@(any,number);MouseButton1Click@();MouseButton2Click@();MouseButton1Down@(number,number);MouseButton1Up@(number,number);MouseButton2Down@(number,number);MouseButton2Up@(number,number);TouchTap@(any)
TextBox|GuiObject||Text:string;PlaceholderText:string;PlaceholderColor3:Color3;TextColor3:Color3;TextSize:number;TextScaled:boolean;TextWrapped:boolean;Font:Enum.Font;ClearTextOnFocus:boolean;MultiLine:boolean;TextEditable:boolean;ShowNativeInput:boolean;CursorPosition:number;SelectionStart:number;TextXAlignment:Enum.TextXAlignment;TextYAlignment:Enum.TextYAlignment;CaptureFocus();ReleaseFocus(boolean?);IsFocused():boolean;FocusLost@(boolean,any);Focused@();ReturnPressedFromOnScreenKeyboard@()
ImageLabel|GuiObject||Image:string;ImageColor3:Color3;ImageTransparency:number;ScaleType:Enum.ScaleType;ImageRectOffset:Vector2;ImageRectSize:Vector2;SliceCenter:Rect;SliceScale:number;TileSize:UDim2;ResampleMode:any
ImageButton|GuiObject||Image:string;ImageColor3:Color3;ImageTransparency:number;ScaleType:Enum.ScaleType;ImageRectOffset:Vector2;ImageRectSize:Vector2;HoverImage:string;PressedImage:string;AutoButtonColor:boolean;Activated@(any,number);MouseButton1Click@();MouseButton2Click@();MouseButton1Down@(number,number);MouseButton1Up@(number,number)
LayerCollector|GuiBase2d||Enabled:boolean;ResetOnSpawn:boolean;ZIndexBehavior:Enum.ZIndexBehavior
ScreenGui|LayerCollector||DisplayOrder:number;IgnoreGuiInset:boolean;ScreenInsets:any
`;
// service / class name lists
const SERVICE_LIST="Workspace Players Lighting ReplicatedStorage ReplicatedFirst ServerStorage ServerScriptService StarterGui StarterPack StarterPlayer Teams SoundService Chat TextChatService RunService UserInputService ContextActionService TweenService HttpService MarketplaceService DataStoreService MessagingService TeleportService CollectionService PhysicsService PathfindingService Debris GuiService TextService BadgeService GroupService LocalizationService VRService ProximityPromptService MemoryStoreService ContentProvider HapticService SocialService PolicyService AnalyticsService Stats InsertService AssetService CoreGui ScriptContext TestService KeyframeSequenceProvider AnimationClipProvider AvatarEditorService Selection StudioService NetworkClient NetworkServer LogService VirtualInputManager RbxAnalyticsService MaterialService TouchInputService VoiceChatService UserService ExperienceService OpenCloudService SelectionService ChangeHistoryService GamePassService NotificationService CaptureService AvatarChatService HttpRbxApiService ScriptService ReflectionService UGCValidationService AdService CookiesService GamepadService PermissionsService SafetyService ExperienceNotificationService LanguageService VideoCaptureService GuidRegistryService CSGDictionaryService NonReplicatedCSGDictionaryService UserGameSettings TimerService StarterPlayerScripts Visit GenericSettings".split(" ");
const CREATABLE="Accessory Accoutrement Actor AdGui AdPortal AirController AlignOrientation AlignPosition AngularVelocity Animation AnimationConstraint AnimationController Animator Annotation ArcHandles Atmosphere Attachment AudioAnalyzer AudioChannelMixer AudioChannelSplitter AudioChorus AudioCompressor AudioDeviceInput AudioDeviceOutput AudioDistortion AudioEcho AudioEmitter AudioEqualizer AudioFader AudioFilter AudioFlanger AudioListener AudioPitchShifter AudioPlayer AudioRecorder AudioReverb AudioTextToSpeech AudioTremolo Backpack BallSocketConstraint Beam BillboardGui BindableEvent BindableFunction BlockMesh BloomEffect BlurEffect BodyAngularVelocity BodyForce BodyGyro BodyPosition BodyThrust BodyVelocity Bone BoolValue BoxHandleAdornment BrickColorValue BubbleChatConfiguration Camera CanvasGroup CFrameValue CharacterMesh ChorusSoundEffect ClickDetector ClimbController Clouds Color3Value ColorCorrectionEffect ColorGradingEffect CompressorSoundEffect ConeHandleAdornment Configuration CornerWedgePart CurveAnimation CylinderHandleAdornment CylinderMesh DataStoreGetOptions DataStoreIncrementOptions DataStoreOptions DataStoreSetOptions Decal DepthOfFieldEffect Dialog DialogChoice DistortionSoundEffect DragDetector Dragger EchoSoundEffect EqualizerSoundEffect EulerRotationCurve Explosion FaceControls FileMesh Fire Flag FlagStand FlangeSoundEffect FloatCurve FloorWire Folder ForceField Frame GroundController Glue Handles Hat Highlight HingeConstraint Hint Hole HopperBin Humanoid HumanoidController HumanoidDescription IKControl ImageButton ImageHandleAdornment ImageLabel IntConstrainedValue IntValue Keyframe KeyframeMarker KeyframeSequence LineForce LineHandleAdornment LinearVelocity LocalScript LocalizationTable ManualGlue ManualWeld MaterialVariant Message MeshPart Model ModuleScript Motor Motor6D NegateOperation NoCollisionConstraint NumberPose NumberValue ObjectValue Pants ParallelRampPart Part ParticleEmitter Path2D PathfindingLink PathfindingModifier PitchShiftSoundEffect Plane PlaneConstraint PointLight Pose PrismaticConstraint ProximityPrompt RayValue RemoteEvent RemoteFunction ReverbSoundEffect RigidConstraint RocketPropulsion RodConstraint RopeConstraint Rotate RotateP RotateV RotationCurve ScreenGui Script ScrollingFrame Seat SelectionBox SelectionSphere Shirt ShirtGraphic SkateboardPlatform Sky Smoke Snap Sound SoundGroup Sparkles SpawnLocation SpecialMesh SphereHandleAdornment SpotLight SpringConstraint StarterGear StringValue SunRaysEffect SurfaceAppearance SurfaceGui SurfaceLight SurfaceSelection Team TerrainDetail TextBox TextButton TextChannel TextChatCommand TextLabel Texture Tool Torque TorsionSpringConstraint TouchTransmitter Trail TremoloSoundEffect TrussPart UIAspectRatioConstraint UICorner UIDragDetector UIFlexItem UIGradient UIGridLayout UIListLayout UIPadding UIPageLayout UIScale UISizeConstraint UIStroke UITableLayout UITextSizeConstraint UnionOperation UniversalConstraint UnreliableRemoteEvent Vector3Value VectorForce VehicleSeat VelocityMotor VideoFrame ViewportFrame WedgePart Weld WeldConstraint Wire WireframeHandleAdornment WorldModel WrapDeformer WrapLayer WrapTarget WrapTextureTransfer TeleportOptions ExperienceInviteOptions ChatInputBarConfiguration ChatWindowConfiguration CylindricalConstraint SlidingBallConstraint AudioLimiter BuoyancySensor ControllerPartSensor SkateboardController VehicleController TrackerStreamAnimation PackageLink PartOperation Sphere AnimationRigData RTAnimationTracker HumanoidRigDescription Status Trail".split(" ");
const ENUM_SRC=``;
const DB_FULL=false;
// <<API_DB_END>>
const DATATYPES=new Set("Vector3 Vector2 CFrame Color3 BrickColor UDim UDim2 Rect Ray Region3 TweenInfo NumberRange NumberSequence ColorSequence Random DateTime Font RaycastParams OverlapParams RaycastResult PhysicalProperties Faces Axes RBXScriptSignal RBXScriptConnection Vector3int16 Vector2int16 Region3int16 NumberSequenceKeypoint ColorSequenceKeypoint PathWaypoint buffer".split(" "));
// named datatype members (type of member; unknown members => any)
const DT_MEMBERS={
 Vector3:"X:number;Y:number;Z:number;Magnitude:number;Unit:Vector3;Cross(Vector3):Vector3;Dot(Vector3):number;Lerp(Vector3,number):Vector3;Angle(Vector3,Vector3?):number;FuzzyEq(Vector3,number?):boolean;Max(...Vector3):Vector3;Min(...Vector3):Vector3;Abs():Vector3;Ceil():Vector3;Floor():Vector3;Sign():Vector3",
 Vector2:"X:number;Y:number;Magnitude:number;Unit:Vector2;Cross(Vector2):number;Dot(Vector2):number;Lerp(Vector2,number):Vector2",
 CFrame:"Position:Vector3;X:number;Y:number;Z:number;LookVector:Vector3;RightVector:Vector3;UpVector:Vector3;Rotation:CFrame;Inverse():CFrame;ToWorldSpace(CFrame):CFrame;ToObjectSpace(CFrame):CFrame;PointToWorldSpace(Vector3):Vector3;PointToObjectSpace(Vector3):Vector3;VectorToWorldSpace(Vector3):Vector3;VectorToObjectSpace(Vector3):Vector3;Lerp(CFrame,number):CFrame;GetComponents():number;ToEulerAnglesXYZ():number;ToOrientation():number",
 Color3:"R:number;G:number;B:number;Lerp(Color3,number):Color3;ToHSV():number;ToHex():string",
 BrickColor:"Name:string;Color:Color3;Number:number;r:number;g:number;b:number",
 UDim2:"X:UDim;Y:UDim;Width:UDim;Height:UDim;Lerp(UDim2,number,number):UDim2",
 UDim:"Scale:number;Offset:number"};
const LIBS={
 math:"abs(number):number;acos(number):number;asin(number):number;atan(number):number;atan2(number,number):number;ceil(number):number;clamp(number,number,number):number;cos(number):number;cosh(number):number;deg(number):number;exp(number):number;floor(number):number;fmod(number,number):number;frexp(number):number;ldexp(number,number):number;lerp(number,number,number):number;log(number,number?):number;log10(number):number;map(number,number,number,number,number):number;max(number,...number):number;min(number,...number):number;modf(number):number;noise(number,number?,number?):number;pow(number,number):number;rad(number):number;random(number?,number?):number;randomseed(number);round(number):number;sign(number):number;sin(number):number;sinh(number):number;sqrt(number):number;tan(number):number;tanh(number):number;pi:number;huge:number",
 string:"byte(string,number?,number?):number;char(...number):string;find(string,string,number?,boolean?):number;format(string,...any):string;gmatch(string,string):any;gsub(string,string,any,number?):string;len(string):number;lower(string):string;match(string,string,number?):string?;rep(string,number,string?):string;reverse(string):string;split(string,string?):{string};sub(string,number?,number?):string;upper(string):string;pack(string,...any):string;packsize(string):number;unpack(string,string,number?):any",
 task:"wait(number?):number;spawn(fnthread,...any):thread;defer(fnthread,...any):thread;delay(number,fnthread,...any):thread;cancel(thread);synchronize();desynchronize()",
 table:"insert(any,any);insert(any,number,any);remove(any,number?):any;find(any,any,number?):number?;concat(any,string?,number?,number?):string;sort(any,fn?);clear(any);clone(any):any;freeze(any):any;isfrozen(any):boolean;unpack(any,number?,number?):any;pack(...any):any;move(any,number,number,number,any?):any;create(number,any?):any;getn(any):number;maxn(any):number",
 os:"time(any?):number;clock():number;date(string?,number?):any;difftime(number,number):number",
 Vector3:"new(number?,number?,number?):Vector3;FromNormalId(any):Vector3;FromAxis(any):Vector3;zero:Vector3;one:Vector3;xAxis:Vector3;yAxis:Vector3;zAxis:Vector3",
 Vector2:"new(number?,number?):Vector2;zero:Vector2;one:Vector2;xAxis:Vector2;yAxis:Vector2",
 CFrame:"new():CFrame;new(Vector3):CFrame;new(Vector3,Vector3):CFrame;new(number,number,number):CFrame;new(number,number,number,number,number,number,number):CFrame;new(number,number,number,number,number,number,number,number,number,number,number,number):CFrame;Angles(number,number,number):CFrame;lookAt(Vector3,Vector3,Vector3?):CFrame;fromEulerAnglesXYZ(number,number,number):CFrame;fromEulerAnglesYXZ(number,number,number):CFrame;fromOrientation(number,number,number):CFrame;fromAxisAngle(Vector3,number):CFrame;identity:CFrame",
 Color3:"new(number?,number?,number?):Color3;fromRGB(number?,number?,number?):Color3;fromHSV(number,number,number):Color3;fromHex(string):Color3",
 UDim2:"new():UDim2;new(number,number,number,number):UDim2;new(UDim,UDim):UDim2;fromScale(number,number):UDim2;fromOffset(number,number):UDim2",
 UDim:"new(number?,number?):UDim",
 TweenInfo:"new(number?,any?,any?,number?,boolean?,number?):TweenInfo",
 BrickColor:"new(number):BrickColor;new(string):BrickColor;new(Color3):BrickColor;new(number,number,number):BrickColor;random():BrickColor"};
const GLOBAL_FNS="print(...any);warn(...any);error(any,number?);assert(any,...any):any;tostring(any):string;tonumber(any,number?):number?;type(any):string;typeof(any):string;select(any,...any):any;pcall(any,...any):boolean;xpcall(any,any,...any):boolean;setmetatable(any,any):any;getmetatable(any):any;rawget(any,any):any;rawset(any,any,any):any;rawequal(any,any):boolean;rawlen(any):number;next(any,any?):any;ipairs(any):any;pairs(any):any;tick():number;time():number;wait(number?):number;spawn(fn);delay(number,fn);unpack(any,number?,number?):any";

// ===== Pass 2: full AST parser (statements, expressions, Luau types) =====
class AstErr extends Error{}
function parseAST(T){
  let p=0;
  const pk=(o=0)=>T[Math.min(p+o,T.length-1)];
  const nx=()=>{const t=T[p];if(t.t!=="eof")p++;return t};
  const is=(v,o=0)=>{const t=pk(o);return(t.t==="kw"||t.t==="sym")&&t.v===v};
  const eat=v=>is(v)?nx():null;
  const need=v=>{if(!is(v))throw new AstErr(`ast: expected '${v}' at ${pk().line}:${pk().col}`);return nx()};
  const name=()=>{const t=pk();if(t.t!=="id")throw new AstErr(`ast: name expected at ${t.line}:${t.col}`);return nx()};
  const atEnd=terms=>{const t=pk();return t.t==="eof"||(t.t==="kw"&&terms.includes(t.v))};

  // ---- types ----
  function type(){
    if(is("|")||is("&"))nx();
    let t=typeAtom();
    while(is("?")||is("|")||is("&")){
      const o=nx();
      if(o.v==="?")t={k:"opt",t};
      else{const r=typeAtom();const kind=o.v==="|"?"union":"inter";t=t.k===kind&&!t.paren?{...t,ts:[...t.ts,r]}:{k:kind,ts:[t,r]}}}
    return t}
  function packList(){ // after '(' consumed; returns [{name,t,vararg}]
    const items=[];
    if(!is(")")){do{
      let nm=null,va=false;
      if(is("...")){nx();va=true}
      if(pk().t==="id"&&is(":",1)){nm=nx().v;nx()}
      items.push({name:nm,t:type(),vararg:va})}while(eat(","))}
    need(")");return items}
  function fnRet(){
    if(is("(")){const save=p;nx();const l=packList();return{pack:l.map(x=>x.t)}}
    return{pack:[type()]}}
  function genericsDecl(){ // <T, U...>
    const g=[];need("<");
    do{const n=name().v;if(eat("..."))g.push(n+"...");else g.push(n);if(eat("=")){type()}}while(eat(","));
    need(">");return g}
  function typeAtom(){
    const t=pk();
    if(is("(")){
      nx();const items=packList();
      if(is("->")){nx();const r=fnRet();return{k:"fn",params:items.filter(i=>!i.vararg),vararg:(items.find(i=>i.vararg)||{}).t||null,ret:r.pack}}
      if(items.length===1&&!items[0].vararg){const x=items[0].t;return{...x,paren:true}}
      return{k:"pack",ts:items.map(i=>i.t)}}
    if(is("<")){const gens=genericsDecl();need("(");const items=packList();need("->");const r=fnRet();return{k:"fn",gens,params:items.filter(i=>!i.vararg),vararg:(items.find(i=>i.vararg)||{}).t||null,ret:r.pack}}
    if(is("{")){
      nx();
      if(is("}")){nx();return{k:"table",props:[],indexer:null}}
      if(is("[")){nx();const kt=type();need("]");need(":");const vt=type();eat(",")||eat(";");need("}");return{k:"table",props:[],indexer:{key:kt,val:vt}}}
      if((pk().t==="id"&&is(":",1))||(pk().t==="id"&&(pk().v==="read"||pk().v==="write")&&pk(1).t==="id"&&is(":",2))||(pk().t==="str"&&is(":",1))){
        const props=[];let indexer=null;
        while(!is("}")){
          if(pk().t==="id"&&(pk().v==="read"||pk().v==="write")&&pk(1).t==="id"&&is(":",2))nx();
          if(is("[")){nx();const kt=type();need("]");need(":");indexer={key:kt,val:type()}}
          else{const n=pk();if(n.t!=="id"&&n.t!=="str")throw new AstErr("ast: bad table type field");nx();need(":");props.push({name:n.t==="str"?n.v:n.v,t:type(),tok:n})}
          if(!eat(",")&&!eat(";"))break}
        need("}");return{k:"table",props,indexer}}
      const el=type();need("}");return{k:"table",props:[],indexer:{key:{k:"name",n:"number"},val:el},array:true}}
    if(is("...")){nx();return type()}
    if(t.t==="str"){nx();return{k:"slit",v:t.v}}
    if(t.t==="kw"&&(t.v==="nil"||t.v==="true"||t.v==="false")){nx();return t.v==="nil"?{k:"name",n:"nil"}:{k:"blit",v:t.v==="true"}}
    if(t.t==="id"){
      nx();
      if(t.v==="typeof"&&is("(")){nx();const e=expr();need(")");return{k:"typeof",e}}
      let n=t.v;const path=[t.v];
      while(is(".")&&pk(1).t==="id"){nx();path.push(nx().v)}
      let args=null;
      if(is("<")){nx();args=[];if(!is(">")){do{args.push(type())}while(eat(","))}need(">")}
      return{k:"name",n:path[path.length-1],path,args,tok:t}}
    throw new AstErr(`ast: type expected at ${t.line}:${t.col}`)}

  // ---- expressions ----
  const BIN={or:[1,1],and:[2,2],"<":[3,3],">":[3,3],"<=":[3,3],">=":[3,3],"~=":[3,3],"==":[3,3],"..":[5,4],"+":[6,6],"-":[6,6],"*":[7,7],"/":[7,7],"//":[7,7],"%":[7,7],"^":[10,9]};
  function expr(lim=0){
    const t=pk();let l;
    if((t.t==="kw"&&t.v==="not")||(t.t==="sym"&&(t.v==="-"||t.v==="#"))){nx();const o=expr(8);l={k:"Un",op:t.v,e:o,tok:t}}
    else l=simple();
    for(;;){const o=pk(),b=(o.t==="kw"||o.t==="sym")&&BIN[o.v];if(!b||b[0]<=lim)break;nx();const r=expr(b[1]);l={k:"Bin",op:o.v,l,r,tok:o}}
    return l}
  function simple(){
    const t=pk();let e;
    if(t.t==="num"){nx();e={k:"Num",v:t.v,tok:t}}
    else if(t.t==="str"){nx();e=t.raw[0]==="`"?{k:"Interp",tok:t}:{k:"Str",v:t.v,tok:t}}
    else if(t.t==="kw"&&t.v==="nil"){nx();e={k:"Nil",tok:t}}
    else if(t.t==="kw"&&(t.v==="true"||t.v==="false")){nx();e={k:"Bool",v:t.v==="true",tok:t}}
    else if(is("...")){nx();e={k:"Vararg",tok:t}}
    else if(is("{"))e=table();
    else if(is("function")){nx();e=funcbody(t,false)}
    else if(is("if")){e=ifexpr()}
    else e=suffixed();
    while(is("::")){const c=nx();e={k:"Cast",e,type:type(),tok:c}}
    return e}
  function ifexpr(){const t=nx();const c=[];const v=[];c.push(expr());need("then");v.push(expr());while(eat("elseif")){c.push(expr());need("then");v.push(expr())}need("else");const el=expr();return{k:"IfExpr",c,v,el,tok:t}}
  function table(){
    const t=need("{");const items=[];
    while(!is("}")){
      if(is("[")){nx();const k=expr();need("]");need("=");items.push({kind:"idx",k,v:expr()})}
      else if(pk().t==="id"&&is("=",1)){const n=nx();nx();items.push({kind:"name",name:n.v,tok:n,v:expr()})}
      else items.push({kind:"arr",v:expr()});
      if(!eat(",")&&!eat(";"))break}
    need("}");return{k:"Table",items,tok:t}}
  function callArgs(){
    if(is("(")){nx();const a=[];if(!is(")")){a.push(expr());while(eat(","))a.push(expr())}need(")");return a}
    if(pk().t==="str"){const t=nx();return[t.raw[0]==="`"?{k:"Interp",tok:t}:{k:"Str",v:t.v,tok:t}]}
    if(is("{"))return[table()];
    throw new AstErr("ast: call args expected")}
  function suffixed(){
    const t=pk();let e;
    if(t.t==="id"){nx();e={k:"Name",name:t.v,tok:t}}
    else if(is("(")){nx();const x=expr();need(")");e={k:"Paren",e:x,tok:t}}
    else throw new AstErr(`ast: unexpected ${t.v} at ${t.line}:${t.col}`);
    for(;;){
      const c=pk();
      if(is(".")){nx();const n=name();e={k:"Index",o:e,name:n.v,tok:n,dot:c}}
      else if(is("[")){nx();const x=expr();need("]");e=x.k==="Str"?{k:"Index",o:e,name:x.v,tok:c,dot:c}:{k:"IndexE",o:e,e:x,tok:c}}
      else if(is(":")){nx();const n=name();const a=callArgs();e={k:"MCall",o:e,name:n.v,args:a,tok:n}}
      else if(is("(")||c.t==="str"||is("{")){const a=callArgs();e={k:"Call",f:e,args:a,tok:c.t==="id"?c:(e.tok||c)}}
      else break}
    return e}
  function funcbody(open,isMethod){
    let gens=null;if(is("<"))gens=genericsDecl();
    need("(");const params=[];let vararg=false,vtype=null;
    if(!is(")")){do{
      if(is("...")){nx();vararg=true;if(eat(":"))vtype=type();break}
      const n=name();let ty=null;if(eat(":"))ty=type();params.push({name:n.v,tok:n,type:ty})}while(eat(","))}
    need(")");let ret=null;
    if(eat(":")){ret=fnRet().pack}
    const body=block(["end"]);need("end");
    return{k:"Func",gens,params,vararg,vtype,ret,body,isMethod,tok:open}}

  // ---- statements ----
  function block(terms){
    const out=[];
    for(;;){
      if(atEnd(terms))return out;
      const t=pk();
      if(t.t==="kw"&&t.v==="return"){
        nx();const vals=[];
        const n=pk();
        if(!(n.t==="eof"||(n.t==="kw"&&["end","else","elseif","until"].includes(n.v))||is(";"))){vals.push(expr());while(eat(","))vals.push(expr())}
        eat(";");out.push({k:"Return",values:vals,tok:t});return out}
      const s=stat();if(s)out.push(s)}}
  const COMP=new Set(["+=","-=","*=","/=","//=","%=","^=","..="]);
  function stat(){
    const t=pk();
    if(is(";")){nx();return null}
    if(is("@")){nx();name();return stat()}
    if(t.t==="kw"){
      switch(t.v){
        case"local":{
          nx();
          if(is("function")){nx();const n=name();const f=funcbody(n,false);return{k:"LocalFunc",name:n.v,tok:n,func:f}}
          const names=[];
          do{const n=name();let ty=null;if(eat(":"))ty=type();names.push({name:n.v,tok:n,type:ty})}while(eat(","));
          const vals=[];if(eat("=")){vals.push(expr());while(eat(","))vals.push(expr())}
          return{k:"Local",names,values:vals,tok:t}}
        case"function":{
          nx();const first=name();let target={k:"Name",name:first.v,tok:first};let m=false;
          while(is(".")){nx();const n=name();target={k:"Index",o:target,name:n.v,tok:n}}
          if(is(":")){nx();const n=name();target={k:"Index",o:target,name:n.v,tok:n};m=true}
          const f=funcbody(t,m);return{k:"FuncStat",target,func:f,tok:t}}
        case"if":{
          nx();const conds=[expr()];need("then");const blocks=[block(["elseif","else","end"])];let els=null;
          while(is("elseif")){nx();conds.push(expr());need("then");blocks.push(block(["elseif","else","end"]))}
          if(eat("else"))els=block(["end"]);need("end");
          return{k:"If",conds,blocks,els,tok:t}}
        case"while":{nx();const c=expr();need("do");const b=block(["end"]);need("end");return{k:"While",cond:c,body:b,tok:t}}
        case"for":{
          nx();const n1=name();
          if(is("=")){nx();const a=expr();need(",");const b=expr();let c=null;if(eat(","))c=expr();need("do");const body=block(["end"]);need("end");return{k:"NumFor",name:n1.v,tok:n1,start:a,stop:b,step:c,body,ftok:t}}
          const names=[n1];while(eat(","))names.push(name());need("in");
          const exprs=[expr()];while(eat(","))exprs.push(expr());need("do");const body=block(["end"]);need("end");
          return{k:"GenFor",names,exprs,body,tok:t}}
        case"repeat":{nx();const b=block(["until"]);need("until");const c=expr();return{k:"Repeat",body:b,cond:c,tok:t}}
        case"do":{nx();const b=block(["end"]);need("end");return{k:"Do",body:b,tok:t}}
        case"break":nx();return{k:"Break",tok:t};
        default:throw new AstErr("ast: unexpected "+t.v)}}
    if(t.t==="id"){
      if(t.v==="continue"&&!["=","(",".",":","[",","].includes(pk(1).v)){nx();return{k:"Continue",tok:t}}
      if(t.v==="export"&&pk(1).v==="type"){nx();return typedecl(true)}
      if(t.v==="type"&&pk(1).t==="id"&&(pk(2).v==="="||pk(2).v==="<"))return typedecl(false)}
    // expression statement / assignment
    const e=suffixed();
    if(is("=")||is(",")||(pk().t==="sym"&&COMP.has(pk().v))){
      const targets=[e];while(eat(","))targets.push(suffixed());
      if(pk().t==="sym"&&COMP.has(pk().v)){const op=nx();const v=expr();return{k:"Assign",targets,values:[v],op:op.v,tok:op}}
      const eq=need("=");const vals=[expr()];while(eat(","))vals.push(expr());
      return{k:"Assign",targets,values:vals,op:"=",tok:eq}}
    return{k:"ExprStat",e,tok:t}}
  function typedecl(exp){
    const kw=nx(); // 'type'
    const n=name();let gens=null;if(is("<"))gens=genericsDecl();
    need("=");const ty=type();return{k:"TypeDecl",name:n.v,gens,type:ty,exp,tok:n}}

  const body=block([]);
  if(pk().t!=="eof")throw new AstErr("ast: trailing tokens");
  return body}

// ===== Pass 2: type system + Roblox API checks + control flow =====
const AN={k:"any"},UNK={k:"unknown"},NEVER={k:"never"};
const prim=(n,lit,o)=>{const t={k:"prim",n};if(lit!==undefined)t.lit=lit;if(o)t.o=o;return t};
const NUM=prim("number"),STR=prim("string"),BOOL=prim("boolean"),NIL=prim("nil"),THR=prim("thread");
const tkey=t=>{switch(t.k){case"prim":return t.n+(t.lit!==undefined?"="+t.lit:"");case"inst":return"I:"+t.n;case"named":return"N:"+t.n;case"enumitem":return"E:"+t.n;case"gen":return"G:"+t.n+t.id;case"fn":return"fn"+(t.id||"");case"table":return"tbl"+(t.id||"");case"signal":return"sig";default:return t.k}};
function union(ts){
  const out=[],seen=new Set();
  const add=t=>{if(t.k==="union"){t.ts.forEach(add);return}if(t.k==="never")return;const k=tkey(t);if(seen.has(k))return;seen.add(k);out.push(t)};
  ts.forEach(add);
  if(out.some(t=>t.k==="any"||t.k==="unknown"))return AN;
  if(!out.length)return NEVER;if(out.length===1)return out[0];
  return{k:"union",ts:out}}
const hasNil=t=>t.k==="prim"&&t.n==="nil"||(t.k==="union"&&t.ts.some(x=>x.k==="prim"&&x.n==="nil"));
const nilOrigin=t=>{if(t.k==="prim")return t.o||"user";const m=t.ts.find(x=>x.k==="prim"&&x.n==="nil");return m&&m.o||"user"};
const removeNil=t=>t.k==="union"?union(t.ts.filter(x=>!(x.k==="prim"&&x.n==="nil"))):(t.k==="prim"&&t.n==="nil"?NEVER:t);
const widen=t=>{if(t.k==="prim"&&t.lit!==undefined)return prim(t.n);if(t.k==="union")return union(t.ts.map(widen));return t};
const truthy=t=>{if(t.k==="union")return union(t.ts.map(truthy));if(t.k==="prim"){if(t.n==="nil")return NEVER;if(t.n==="boolean"){if(t.lit===false)return NEVER;if(t.lit===true)return t;return prim("boolean",true)}}return t};
const falsy=t=>{if(t.k==="any"||t.k==="unknown")return AN;if(t.k==="union")return union(t.ts.map(falsy));if(t.k==="prim"){if(t.n==="nil")return t;if(t.n==="boolean"){if(t.lit===true)return NEVER;return prim("boolean",false)}}return NEVER};
function show(t){
  switch(t.k){
    case"any":return"any";case"unknown":return"unknown";case"never":return"never";
    case"prim":return t.lit!==undefined?(t.n==="string"?JSON.stringify(t.lit):String(t.lit)):t.n;
    case"inst":return t.n;case"named":return t.n;case"enumitem":return"Enum."+t.n;case"gen":return t.n;
    case"union":{const nn=t.ts.filter(x=>!(x.k==="prim"&&x.n==="nil"));const o=nn.length!==t.ts.length;const s=nn.map(show).join(" | ");return o?(nn.length>1?`(${s})?`:s+"?"):s}
    case"fn":return"function";case"table":return t.indexer&&!t.props.size?`{${show(t.indexer.val)}}`:"table";case"signal":return"RBXScriptSignal";
    default:return t.k}}
function lev(a,b){const m=[];for(let i=0;i<=a.length;i++){m[i]=[i];}for(let j=0;j<=b.length;j++)m[0][j]=j;for(let i=1;i<=a.length;i++)for(let j=1;j<=b.length;j++)m[i][j]=Math.min(m[i-1][j]+1,m[i][j-1]+1,m[i-1][j-1]+(a[i-1]===b[j-1]?0:1));return m[a.length][b.length]}
function suggest(n,list){let best=null,bd=99;const ln=n.toLowerCase();for(const c of list){const d=lev(ln,c.toLowerCase());if(d<bd){bd=d;best=c}}return best&&bd<=Math.max(1,Math.min(3,Math.floor(n.length/3)))?best:null}

// ---- API DB build ----
const CLS=new Map();
function dtype(s){
  s=s.trim();if(!s)return AN;
  if(s.endsWith("?"))return union([dtype(s.slice(0,-1)),prim("nil",undefined,"api")]);
  if(s[0]==="{"&&s.endsWith("}")){return{k:"table",props:new Map(),indexer:{key:NUM,val:dtype(s.slice(1,-1))},arr:true}}
  switch(s){case"any":return AN;case"number":return NUM;case"string":return STR;case"boolean":return BOOL;case"nil":return NIL;case"thread":return THR;case"fn":return{k:"fn",any:true};case"fnthread":return union([{k:"fn",any:true},THR])}
  if(s.startsWith("Enum."))return{k:"enumitem",n:s.slice(5)};
  if(DATATYPES.has(s))return{k:"named",n:s};
  return{k:"inst",n:s}}
function parseMembers(src){
  const m=new Map();
  for(const raw of src.split(";")){
    const x=raw.trim();if(!x)continue;
    let mm;
    if((mm=/^(\w+)@\((.*)\)$/.exec(x))){const a=mm[2]?splitTop(mm[2]):[];const va=a.length&&a[a.length-1].startsWith("...");m.set(mm[1],{kind:"event",args:(va?a.slice(0,-1):a).map(dtype),vararg:va});continue}
    if((mm=/^(\w+)\((.*?)\)(?::(.+))?$/.exec(x))){
      const ps=mm[2]?splitTop(mm[2]):[];let va=null;const params=[];
      for(const p of ps){if(p.startsWith("..."))va=dtype(p.slice(3));else{const t=dtype(p);params.push({t,opt:p.endsWith("?")})}}
      const fnT={k:"fn",params,vararg:va,ret:mm[3]?[dtype(mm[3])]:[],known:true};
      const prev=m.get(mm[1]);
      if(prev&&prev.kind==="method"){prev.fn.overloads=prev.fn.overloads||[{...prev.fn,overloads:undefined}];prev.fn.overloads.push(fnT)}
      else m.set(mm[1],{kind:"method",fn:fnT});continue}
    if((mm=/^(\w+):(.+)$/.exec(x))){m.set(mm[1],{kind:"prop",t:dtype(mm[2])});continue}}
  return m}
function splitTop(s){const out=[];let d=0,cur="";for(const c of s){if(c==="{")d++;if(c==="}")d--;if(c===","&&d===0){out.push(cur);cur=""}else cur+=c}if(cur)out.push(cur);return out}
for(const line of API_SRC.split("\n")){
  if(!line.trim())continue;const [n,par,fl,mem]=line.split("|");
  CLS.set(n,{n,parent:par||null,full:fl.includes("F"),members:parseMembers(mem||""),lower:null})}
for(const c of CLS.values()){c.lower=new Set([...c.members.keys()].map(k=>k.toLowerCase()))}
const CREATABLE_SET=new Set(CREATABLE),SERVICE_SET=new Set(SERVICE_LIST);
const ENUMS=new Map();for(const ln of ENUM_SRC.split("\n")){const p=ln.split("|");if(p.length===2&&p[0].trim())ENUMS.set(p[0].trim(),new Set(p[1].split(",").filter(Boolean)))}
const chain=n=>{const out=[];let c=CLS.get(n);if(!c){out.push(null);return out}while(c){out.push(c);c=c.parent?CLS.get(c.parent):null}return out};
function isSub(s,d){if(s===d)return true;if(d==="Instance")return true;let c=CLS.get(s);if(!c)return true;while(c){if(c.n===d)return true;if(!c.parent)return false;c=CLS.get(c.parent);if(!c)return true}return false}
function lookupMember(cls,name){
  for(const c of chain(cls)){if(!c)return{unknownClass:true};if(c.members.has(name))return{m:c.members.get(name)}}
  return null}
function knownLower(cls,name){const l=name.toLowerCase();for(const c of chain(cls)){if(!c)return true;if(c.lower.has(l))return true}return false}
const LIBT=new Map(),DTT=new Map();
for(const[k,v]of Object.entries(LIBS))LIBT.set(k,parseMembers(v));
for(const[k,v]of Object.entries(DT_MEMBERS))DTT.set(k,parseMembers(v));
const GFN=parseMembers(GLOBAL_FNS);
const STRM=parseMembers(LIBS.string);
const CLIENT_M=new Set(["LocalPlayer","RenderStepped","FireServer","InvokeServer","OnClientEvent","OnClientInvoke"]);
const DSM=new Set(["GetAsync","SetAsync","UpdateAsync","IncrementAsync","RemoveAsync"]);
const HOT_SIG=/(Heartbeat|RenderStepped|Stepped|PreRender|PreSimulation|PostSimulation|PreAnimation)$/;
const SERVER_M=new Set(["OnServerEvent","FireClient","FireAllClients","InvokeClient","OnServerInvoke","LoadCharacter"]);
const SERVER_SVC=new Set(["ServerStorage","ServerScriptService","DataStoreService","MessagingService","MemoryStoreService"]);
const CLIENT_SVC=new Set(["UserInputService","ContextActionService","VRService","GuiService","HapticService"]);

function assignable(s,d){
  if(s===d)return true;
  if(s.k==="any"||d.k==="any"||d.k==="unknown"||s.k==="unknown"||s.k==="never")return true;
  if(s.k==="union")return s.ts.every(x=>assignable(x,d));
  if(d.k==="union")return d.ts.some(x=>assignable(s,x));
  if(d.k==="gen"||s.k==="gen")return s.k==="gen"&&d.k==="gen"&&s.n===d.n&&s.id===d.id;
  if(s.k==="prim"&&d.k==="prim"){if(s.n!==d.n)return false;if(d.lit!==undefined)return s.lit===d.lit;return true}
  if(s.k==="inst"&&d.k==="inst")return isSub(s.n,d.n);
  if(s.k==="named"&&d.k==="named")return s.n===d.n;
  if(s.k==="enumitem"&&d.k==="enumitem")return s.n===d.n;
  if(s.k==="fn"&&d.k==="fn")return true;
  if(s.k==="signal"||d.k==="signal")return s.k===d.k;
  if(s.k==="table"&&d.k==="table"){
    for(const[n,pd]of d.props){const ps=s.props.get(n);if(!ps){if(!s.open&&!hasNil(pd.t)&&!pd.opt)return false}else if(!assignable(ps.t,pd.t))return false}
    if(d.indexer&&s.indexer&&!assignable(s.indexer.val,d.indexer.val))return false;
    return true}
  return false}

function contractDiags(shared){
  const out=[];
  for(const c of shared.calls){
    for(const h of shared.handlers){
      if(h.key!==c.key||h.dir!==c.dir)continue;
      c.args.forEach((a,i)=>{const p=h.params[i];if(p&&p.t&&!assignable(a,p.t))out.push({severity:"error",rule:"remote-contract",line:c.tok.line,col:c.tok.col,file:c.file,message:`Remote '${c.key}': handler (${h.file||"main"}, line ${h.tok.line}) param '${p.name}' ko ${show(p.t)} chahiye, par ${c.kind}() se ${show(a)} bheja ja raha hai`})});
      if(h.params.length&&c.args.length>h.params.length&&!h.vararg)out.push({severity:"warning",rule:"remote-contract-count",line:c.tok.line,col:c.tok.col,file:c.file,message:`Remote '${c.key}': ${c.kind}() ${c.args.length} values bhejta hai par handler sirf ${h.params.length} leta hai`});
      const req=h.params.filter(p=>p.t&&!p.opt).length;
      if(c.args.length<req)out.push({severity:"warning",rule:"remote-contract-count",line:c.tok.line,col:c.tok.col,file:c.file,message:`Remote '${c.key}': handler ko kam se kam ${req} annotated argument chahiye, ${c.kind}() sirf ${c.args.length} bhejta hai`})}}
  return out}
function analyze(T,src,opts={}){
  const diags={error:[],warning:[],info:[]};
  const m0=/^\s*--!(strict|nonstrict|nocheck)/m.exec(src.split("\n").slice(0,5).join("\n"));
  const mode=m0?m0[1]:"nonstrict";
  if(mode==="nocheck")return{diags,mode,ran:false};
  let ast;try{ast=parseAST(T)}catch(e){return{diags,mode,ran:false,reason:String(e.message||e)}}
  const strict=mode==="strict";
  const shared=opts.shared||{handlers:[],calls:[],exports:new Map(),stack:[]};
  let peekDepth=0;
  const emit=(sev,rule,tok,msg)=>{if(peekDepth>0)return;const l=diags[sev];const key=rule+tok.line+":"+tok.col+msg;if(emit.seen.has(key))return;emit.seen.add(key);const d={line:tok.line,col:tok.col,rule,severity:sev,message:msg};if(opts.file)d.file=opts.file;l.push(d)};emit.seen=new Set();
  const ERR=(r,t,m)=>emit("error",r,t,m),WARN=(r,t,m)=>emit("warning",r,t,m),INFO=(r,t,m)=>emit("info",r,t,m);
  // --- scopes ---
  let bid=0;let scope={vars:new Map(),parent:null};
  const pushS=()=>{scope={vars:new Map(),parent:scope}};const popS=()=>{scope=scope.parent};
  const lookup=n=>{for(let s=scope;s;s=s.parent)if(s.vars.has(n))return s.vars.get(n);return null};
  const bind=(name,t,o={})=>{const b={id:++bid,name,t,loopLevel:(typeof loopDepth==='number'?loopDepth:0),...o};scope.vars.set(name,b);return b};
  const assignedNames=new Set();
  (function scan(n){if(!n||typeof n!=="object")return;if(Array.isArray(n)){n.forEach(scan);return}
    if(n.k==="Assign")for(const t of n.targets)if(t.k==="Name")assignedNames.add(t.name);
    for(const k in n){if(k!=="tok"&&k!=="dot"&&typeof n[k]==="object")scan(n[k])}})(ast);
  // --- narrowing (path keyed) ---
  const nar=new Map();let gid=0;
  const pathKey=n=>{if(n.k==="Name"){const b=lookup(n.name);return b?"b"+b.id:"g:"+n.name}if(n.k==="Index"){const p=pathKey(n.o);return p?p+"."+n.name:null}if(n.k==="Paren")return pathKey(n.e);return null};
  const applyN=(list)=>{const saved=[];for(const[k,t]of list){saved.push([k,nar.has(k)?nar.get(k):undefined]);if(t)nar.set(k,t);else nar.delete(k)}return()=>{for(const[k,o]of saved.reverse()){if(o===undefined)nar.delete(k);else nar.set(k,o)}}};
  const invalidate=k=>{for(const key of [...nar.keys()])if(key===k||key.startsWith(k+"."))nar.delete(key)};
  // --- aliases / generics ---
  const aliases=new Map();let genStack=[];let resolving=new Set();
  (function reg(b){for(const s of b){if(s.k==="TypeDecl")aliases.set(s.name,s);for(const k of["body","blocks","els"]){const v=s[k];if(Array.isArray(v)){if(v.length&&v[0]&&v[0].k)reg(v);else v.forEach(x=>Array.isArray(x)&&reg(x))}}if(s.func)reg(s.func.body)}})(ast);
  const rt=n=>{
    if(!n)return AN;
    switch(n.k){
      case"name":{
        if(n.path&&n.path.length>1){if(n.path[0]==="Enum")return{k:"enumitem",n:n.path[1]};return AN}
        for(let i=genStack.length-1;i>=0;i--)if(genStack[i].has(n.n))return genStack[i].get(n.n);
        const al=aliases.get(n.n);
        if(al){if(resolving.has(n.n))return AN;resolving.add(n.n);
          const gm=new Map();if(al.gens)al.gens.forEach((g,i)=>gm.set(g.replace("...",""),n.args&&n.args[i]?rt(n.args[i]):{k:"gen",n:g,id:++gid}));
          genStack.push(gm);const r=rt(al.type);genStack.pop();resolving.delete(n.n);return r}
        switch(n.n){case"number":return NUM;case"string":return STR;case"boolean":return BOOL;case"nil":return NIL;case"any":return AN;case"unknown":return UNK;case"never":return NEVER;case"thread":return THR;
          case"table":return{k:"table",props:new Map(),indexer:null,open:true};case"function":return{k:"fn",any:true}}
        if(CLS.has(n.n)||CREATABLE_SET.has(n.n)||SERVICE_SET.has(n.n))return{k:"inst",n:n.n};
        if(DATATYPES.has(n.n))return{k:"named",n:n.n};
        return AN}
      case"opt":return union([rt(n.t),prim("nil",undefined,"user")]);
      case"union":return union(n.ts.map(rt));
      case"inter":return AN;
      case"slit":return prim("string",n.v);
      case"blit":return prim("boolean",n.v);
      case"typeof":return AN;
      case"pack":return AN;
      case"fn":{
        const gm=new Map();if(n.gens)n.gens.forEach(g=>gm.set(g.replace("...",""),{k:"gen",n:g,id:++gid}));
        genStack.push(gm);
        const f={k:"fn",gens:n.gens?[...gm.values()]:null,params:n.params.map(p=>{const t=rt(p.t);return{name:p.name,t,opt:hasNil(t)}}),vararg:n.vararg?rt(n.vararg):null,ret:n.ret.map(rt)};
        genStack.pop();return f}
      case"table":{
        const props=new Map();for(const p of n.props){const t=rt(p.t);props.set(p.name,{t,opt:hasNil(t)})}
        return{k:"table",props,indexer:n.indexer?{key:rt(n.indexer.key),val:rt(n.indexer.val)}:null,arr:!!n.array}}
    }
    return AN};
  // --- helpers ---
  const mismatch=(rule,tok,msg)=>ERR(rule,tok,msg);
  const softNil=(t,d)=>t.k==="union"&&hasNil(t)&&nilOrigin(t)!=="user"&&assignable(removeNil(t),d);
  const reportMis=(rule,tok,t,d,msg)=>{
    if(softNil(t,d)){const m=msg+" (Roblox API ye value nil bhi de sakta hai — nil-check karo)";if(strict)ERR(rule,tok,m);else INFO("api-nil-"+rule,tok,m)}
    else ERR(rule,tok,msg)};
  const isMulti=n=>n&&(n.k==="Call"||n.k==="MCall"||n.k==="Vararg");
  const fnInfo={stack:[]};
  const ctxUse={client:[],server:[],guard:false};
  const noteCtx=(kind,tok,what)=>{if(ctxUse[kind].length<30)ctxUse[kind].push({tok,what})};
  let loopDepth=0,hotDepth=0;const cbStack=[],pcallStack=[];let stmtCall=null,localCap=null;
  const ds={write:null,set:null,get:null,update:false};
  let exportType=null;
  const lastName=n=>!n?null:n.k==="Name"?n.name:n.k==="Index"?n.name:n.k==="Paren"?lastName(n.e):((n.k==="MCall"&&(n.name==="WaitForChild"||n.name==="FindFirstChild")&&n.args[0]&&n.args[0].k==="Str")?n.args[0].v:null);
  const capOf=n=>localCap&&localCap.node===n?localCap.name:null;
  const noteYield=(tok,what)=>{const top=cbStack[cbStack.length-1];if(top&&top.hot)WARN("yield-in-hot-callback",tok,`${what} yield karta hai — ${top.sig||"per-frame"} callback me yield nahi karna chahiye (frames pile up / drop hote hain)`)};
  // context kind
  let ctxKind=opts.context||null;
  {const mc=/--@context\s*[:=]?\s*(client|server|module|shared)/i.exec(src);if(mc)ctxKind=mc[1].toLowerCase();
   if(!ctxKind&&opts.name){const nm=String(opts.name);if(/\.client\.|LocalScript/i.test(nm))ctxKind="client";else if(/\.server\.|ServerScript/i.test(nm))ctxKind="server";else if(/ModuleScript|\.module\./i.test(nm))ctxKind="module"}
   if(ctxKind==="shared")ctxKind="module"}
  function nilAccess(t,node,what){
    if(!hasNil(t))return;
    const o=nilOrigin(t);
    if(t.k==="prim"){if(t.n==="nil"&&o==="user")ERR("nil-access",node.tok,`${what}: value nil hai`);return}
    if(o==="user")ERR("nil-access",node.tok,`${what}: type '${show(t)}' me nil ho sakta hai — pehle nil-check karo (if x then ... end)`);
    else if(o==="api"){if(strict)ERR("nil-access",node.tok,`${what}: Roblox API ye value nil bhi de sakta hai ('${show(t)}') — nil-check karo`);else INFO("api-nil-access",node.tok,`${what}: Roblox API ye value nil bhi de sakta hai ('${show(t)}'); nil-check karna safe rahega`)}
    else if(strict)ERR("nil-access",node.tok,`${what}: type '${show(t)}' nil ho sakta hai`)}
  const pathName=n=>n.k==="Name"?n.name:(n.k==="Index"?pathName(n.o)+"."+n.name:(n.k==="Paren"?pathName(n.e):"expr"));
  // member access on a type
  function member(ot,name,node,mode){
    switch(ot.k){
      case"any":case"unknown":case"never":return AN;
      case"union":{
        nilAccess(ot,node,`'${pathName(node.o||node)}'.${name}`);
        const nn=removeNil(ot);if(nn.k==="never")return AN;
        if(nn.k==="union")return union(nn.ts.map(x=>member(x,name,node,mode)));
        return member(nn,name,node,mode)}
      case"prim":
        if(ot.n==="string"){if(STRM.has(name)){const sm=STRM.get(name);return sm.kind==="method"?{...sm.fn,params:sm.fn.params.slice(1),self:true,label:"string:"+name}:AN}ERR("unknown-member",node.tok,`string me '${name}' naam ka method nahi hai`+(suggest(name,[...STRM.keys()])?` — shayad '${suggest(name,[...STRM.keys()])}'?`:""));return AN}
        if(ot.n==="nil"){nilAccess(ot,node,`'${pathName(node.o||node)}'.${name}`);return AN}
        ERR("index-primitive",node.tok,`'${pathName(node.o||node)}' ${ot.n} hai — usme '.${name}' index nahi kar sakte`);return AN;
      case"inst":{
        const r=lookupMember(ot.n,name);
        if(r&&r.m){const m=r.m;
          if(m.kind==="prop"){if(name==="Parent"&&m.t.k==="union"){return union(m.t.ts.map(x=>x.k==="prim"&&x.n==="nil"?prim("nil",undefined,"parent"):x))}return m.t}
          if(m.kind==="method")return{...m.fn,self:true,label:`${ot.n}:${name}`};
          if(m.kind==="event")return{k:"signal",args:m.args,vararg:m.vararg,label:`${ot.n}.${name}`,sig:name,global:SERVICE_SET.has(ot.n)||ot.n==="Workspace"||ot.n==="DataModel",hot:HOT_SIG.test(name)}}
        if(r&&r.unknownClass)return AN;
        if(!knownLower(ot.n,name)){const c=CLS.get(ot.n);
          const all=[];for(const x of chain(ot.n))if(x)for(const k of x.members.keys())all.push(k);
          const sg=suggest(name,all);
          if((ot.fresh&&c&&c.full)||(DB_FULL&&strict&&c&&ot.n!=="Instance"))ERR("unknown-member",node.tok,`${ot.n} me '${name}' naam ka member nahi hai (validator ki ${ot.n} member list me nahi)`+(sg?` — shayad '${sg}'?`:""));}
        return AN}
      case"table":{
        const p=protoGet(ot,name);if(p)return p.t;
        if(ot.indexer&&(ot.indexer.key.k==="prim"&&ot.indexer.key.n==="string"||ot.indexer.key.k==="any"))return ot.indexer.val;
        if(!ot.open&&!ot.indexer&&ot.props.size){const sg=suggest(name,[...ot.props.keys()]);(strict?ERR:WARN)("unknown-field",node.tok,`table type me '${name}' field declare nahi hai`+(sg?` — shayad '${sg}'?`:""))}
        return AN}
      case"named":{const dm=DTT.get(ot.n);if(dm&&dm.has(name)){const m=dm.get(name);return m.kind==="prop"?m.t:{...m.fn,self:true,label:`${ot.n}:${name}`}}return AN}
      case"enumroot":{if(ENUMS.size&&!ENUMS.has(name)){const sg=suggest(name,[...ENUMS.keys()]);ERR("unknown-enum",node.tok,`Enum.${name} Roblox me nahi hai`+(sg?` — shayad '${sg}'?`:""))}return{k:"enumtype",n:name}}
      case"enumtype":{const items=ENUMS.get(ot.n);if(items&&!items.has(name)){const sg=suggest(name,[...items]);ERR("unknown-enum-item",node.tok,`Enum.${ot.n}.${name} nahi hai`+(sg?` — shayad '${sg}'?`:""))}return{k:"enumitem",n:ot.n}}
      case"lib":{const lm=LIBT.get(ot.n);if(lm&&lm.has(name)){const m=lm.get(name);return m.kind==="prop"?m.t:{...m.fn,label:`${ot.n}.${name}`}}
        if(lm&&(ot.n==="math"||ot.n==="string"||ot.n==="task"||ot.n==="os")){const sg=suggest(name,[...lm.keys()]);ERR("unknown-member",node.tok,`${ot.n} library me '${name}' nahi hai`+(sg?` — shayad '${sg}'?`:""))}
        return AN}
      case"signal":{
        const cb={k:"fn",params:ot.args.map(t=>({name:"arg",t,opt:true})),vararg:ot.vararg?AN:null,ret:[],isCallback:true,fixedArity:!ot.vararg,sig:ot.sig,hot:ot.hot,global:ot.global};
        if(name==="Connect"||name==="Once"||name==="ConnectParallel")return{k:"fn",params:[{name:"callback",t:cb}],ret:[{k:"inst",n:"RBXScriptConnection"}],known:true,label:`${ot.label}:${name}`,self:true};
        if(name==="Wait")return{k:"fn",params:[],ret:[AN],known:true,self:true,label:`${ot.label}:Wait`};
        ERR("unknown-member",node.tok,`signal ${ot.label} me '${name}' nahi hai (Connect/Once/Wait use karo)`);return AN}
      default:return AN}}
  const instOf=tb=>tb.inst||(tb.inst={k:"table",open:true,props:new Map(),proto:tb,shape:true,isInst:true});
  const protoGet=(tb,name)=>{for(let t=tb;t;t=t.proto){if(t.props.has(name))return t.props.get(name)}return null};
  // --- expressions ---
  function ex(n,expected){
    switch(n.k){
      case"Num":return NUM;
      case"Str":return prim("string",n.v);
      case"Interp":return STR;
      case"Nil":return NIL;
      case"Bool":return prim("boolean",n.v);
      case"Vararg":return AN;
      case"Paren":{const t=ex(n.e);return isMulti(n.e)?t:t}
      case"Name":{
        const b=lookup(n.name);
        if(b){const k="b"+b.id;return nar.has(k)?nar.get(k):b.t}
        switch(n.name){
          case"game":return{k:"inst",n:"DataModel"};
          case"workspace":case"Workspace":return{k:"inst",n:"Workspace"};
          case"script":return{k:"inst",n:"LuaSourceContainer"};
          case"Enum":return{k:"enumroot"};
          case"math":case"string":case"task":case"os":case"table":case"Vector3":case"Vector2":case"CFrame":case"Color3":case"UDim2":case"UDim":case"TweenInfo":case"BrickColor":return{k:"lib",n:n.name};
          case"Instance":return{k:"lib",n:"Instance"}}
        if(GFN.has(n.name)){const m=GFN.get(n.name);return m.kind==="method"?{...m.fn,label:n.name}:AN}
        return AN}
      case"Func":return fnLiteral(n,expected);
      case"Table":return tableLit(n,expected);
      case"Cast":{
        const f=ex(n.e);const to=rt(n.type);
        if(!(assignable(f,to)||assignable(to,f)||f.k==="any"||to.k==="any")&&!(f.k==="union"&&f.ts.some(x=>assignable(x,to)||assignable(to,x))))
          ERR("invalid-cast",n.tok,`Invalid type cast: '${show(widen(f))}' ko '${show(to)}' me cast nahi kar sakte`);
        return(to.k==="inst"&&f.rname)?{...to,rname:f.rname}:to}
      case"IfExpr":{
        const ts=[];const undo=[];
        for(let i=0;i<n.c.length;i++){const nr=condNar(n.c[i]);ex(n.c[i]);const u=applyN(nr.t);ts.push(ex(n.v[i]));u();undo.push(...nr.f)}
        const u=applyN(undo);ts.push(ex(n.el));u();return union(ts.map(widen))}
      case"Un":{
        const t=ex(n.e);
        if(n.op==="not")return BOOL;
        if(n.op==="-"){checkArith("-",t,NUM,n,n.e);return t.k==="named"?t:(t.k==="prim"&&t.n==="number"?NUM:AN)}
        if(n.op==="#"){const w=widen(t);if(w.k==="prim"&&(w.n==="number"||w.n==="boolean"||w.n==="nil"))ERR("invalid-length",n.tok,`'#' ${w.n} par kaam nahi karta (string ya table chahiye)`);return NUM}
        return AN}
      case"Bin":return bin(n);
      case"Index":{
        const key=pathKey(n);if(key&&nar.has(key)){ex(n.o);return nar.get(key)}
        const ot=ex(n.o);
        if(ot.k==="lib"&&ot.n==="Instance"){return AN}
        if(CLIENT_M.has(n.name))noteCtx("client",n.tok,n.name);if(SERVER_M.has(n.name))noteCtx("server",n.tok,n.name);
        if(ot.k==="inst"&&ot.n==="DataModel"){const r=lookupMember("DataModel",n.name);if(SERVICE_SET.has(n.name))return{k:"inst",n:n.name};if(n.name==="PlaceId"||n.name==="GameId"||n.name==="CreatorId")return NUM;if(n.name==="JobId")return STR;return AN}
        {const r0=member(ot,n.name,n,"read");return r0.k==="any"&&!r0.rname?{k:"any",rname:n.name}:r0}}
      case"IndexE":{const ot=ex(n.o);ex(n.e);
        if(ot.k==="table"&&ot.indexer)return ot.indexer.val;
        if(ot.k==="union"){nilAccess(ot,n,`'${pathName(n.o)}'[...]`)}
        return AN}
      case"Call":return call(n);
      case"MCall":return mcall(n);
    }
    return AN}
  function fnLiteral(n,expected){
    const sLoop=loopDepth,sHot=hotDepth;if(!n.inline){loopDepth=0;hotDepth=expected&&expected.hot?1:0}
    const isCb=!!(expected&&expected.k==="fn"&&expected.isCallback);
    if(isCb)cbStack.push({sig:expected.sig,hot:!!expected.hot,global:!!expected.global});
    const saved=new Map(nar);
    for(const k of[...nar.keys()]){if(k.includes(".")){nar.delete(k);continue}const id=+k.slice(1);for(let s=scope;s;s=s.parent)for(const b of s.vars.values())if(b.id===id&&assignedNames.has(b.name))nar.delete(k)}
    const gm=new Map();if(n.gens)n.gens.forEach(g=>gm.set(g.replace("...",""),{k:"gen",n:g,id:++gid}));
    genStack.push(gm);
    const f={k:"fn",gens:n.gens?[...gm.values()]:null,params:[],vararg:n.vararg?(n.vtype?rt(n.vtype):AN):null,ret:n.ret?n.ret.map(rt):null,declared:!!n.ret,allAnnotated:n.params.every(p=>p.type)};
    const optIdiom=new Set();
    walk(n.body,nd=>{
      if(nd.k==="Func"&&nd!==n)return;
      if(nd.k==="Bin"&&(nd.op==="or"||nd.op==="and")&&nd.l.k==="Name")optIdiom.add(nd.l.name);
      if(nd.k==="Bin"&&(nd.op==="=="||nd.op==="~=")&&((nd.l.k==="Name"&&nd.r.k==="Nil")||(nd.r.k==="Name"&&nd.l.k==="Nil")))optIdiom.add(nd.l.k==="Name"?nd.l.name:nd.r.name);
      if(nd.k==="If")nd.conds.forEach(c=>{if(c.k==="Name")optIdiom.add(c.name);if(c.k==="Un"&&c.op==="not"&&c.e.k==="Name")optIdiom.add(c.e.name)});
      if(nd.k==="IfExpr")nd.c.forEach(c=>{if(c.k==="Name")optIdiom.add(c.name)})});
    pushS();
    if(n.isMethod)bind("self",n.selfType||AN,{});
    n.params.forEach((p,i)=>{
      let t;
      if(p.type)t=rt(p.type);else if(expected&&expected.k==="fn"&&expected.params&&expected.params[i])t=expected.params[i].t;else t=AN;
      f.params.push({name:p.name,t,opt:hasNil(t)||!p.type,softOpt:optIdiom.has(p.name)});bind(p.name,t,{decl:!!p.type,tok:p.tok})});
    if(expected&&expected.k==="fn"&&expected.isCallback&&expected.fixedArity&&n.params.length>expected.params.length)
      WARN("callback-arity",n.tok,`callback ${n.params.length} parameters leta hai par event sirf ${expected.params.length} deta hai`);
    const rec={ret:f.ret,returns:[],bareReturn:false,fn:f};fnInfo.stack.push(rec);
    block(n.body);
    fnInfo.stack.pop();popS();genStack.pop();
    if(!f.ret){f.ret=rec.returns.length?[union(rec.returns.map(widen))]:[]}
    for(const[k,v]of saved)nar.set(k,v);for(const k of[...nar.keys()])if(!saved.has(k))nar.delete(k);
    if(isCb)cbStack.pop();loopDepth=sLoop;hotDepth=sHot;
    return f}
  function tableLit(n,expected){
    let exp=expected;if(exp&&exp.k==="union")exp=exp.ts.find(x=>x.k==="table")||null;
    for(const it of n.items){
      if(it.kind==="idx"){ex(it.k);ex(it.v)}
      else if(it.kind==='name'&&it.v.k==='Func'&&!(exp&&exp.k==='table'&&exp.props.has(it.name))){it.vt=ex(it.v)}
      else{const et=exp&&exp.k==="table"?(it.kind==="name"&&exp.props.has(it.name)?exp.props.get(it.name).t:(it.kind==="arr"&&exp.indexer?exp.indexer.val:null)):null;
        const vt=exArg(it.v,et);
        if(et&&exp&&!assignable(vt,et)){
          const where=it.kind==="name"?`${exp.label||"table"}.${it.name}`:`${exp.label||"table"}[element]`;
          ERR("type-mismatch",(it.tok||it.v.tok||n.tok),`${where} expects ${show(et)}, got ${show(widen(vt))}`)}}}
    if(exp&&exp.k==="table"){const have=new Set(n.items.filter(i=>i.kind==="name").map(i=>i.name));
      for(const[pn,p]of exp.props)if(!have.has(pn)&&!p.opt&&!hasNil(p.t)&&!n.items.some(i=>i.kind==="idx"))ERR("missing-field",n.tok,`${exp.label||"table"} me required field '${pn}' missing hai`)}
    const props=new Map();
    for(const it of n.items)if(it.kind==="name"&&it.v.k==="Func"){const ft=it.vt||ex(it.v);if(ft&&ft.k==="fn")props.set(it.name,{t:ft})}
    return{k:"table",props,indexer:null,open:true,lit:true,shape:true}}
  function exArg(n,expected){
    if(n.k==="Table"||n.k==="Func")return ex(n,expected);
    const t=ex(n,expected);return t}
  function checkAssign(valueNode,declared,tok,label,rule="type-mismatch"){
    let d=declared;
    if(valueNode.k==="Table"&&(d.k==="table"||(d.k==="union"&&d.ts.some(x=>x.k==="table")))){
      const tt=d.k==="union"?d.ts.find(x=>x.k==="table"):d;if(label)tt.label=label;ex(valueNode,d);return d}
    const t=ex(valueNode,d);
    if(!assignable(t,d))reportMis(rule,tok,t,d,`Type '${show(t.k==="union"?t:widen(t))}' ko '${show(d)}' me assign nahi kar sakte${label?` (${label})`:""}`);
    return t}
  function checkArith(op,t,other,node,sub){
    const bad=x=>x.k==="prim"&&(x.n==="string"||x.n==="boolean")||x.k==="fn"||(x.k==="table"&&!x.open);
    const w=t;
    if(w.k==="union"){
      if(hasNil(w)){nilAccess(w,sub||node,`arithmetic '${op}' operand`)}
      const nn=removeNil(w);const mem=nn.k==="union"?nn.ts:[nn];
      if(mem.some(bad)){ERR("arith-type",node.tok,`'${op}' operand ka type '${show(w)}' arithmetic ke liye valid nahi (number chahiye)`);return false}
      return true}
    if(w.k==="prim"&&w.n==="nil"){if(nilOrigin(w)==="user"&&!strict)return true;ERR("arith-type",node.tok,`'${op}' operand nil hai`);return false}
    if(bad(w)){ERR("arith-type",node.tok,`Arithmetic '${op}' me ${show(widen(w))} operand valid nahi — number chahiye${w.k==="prim"&&w.n==="string"?" (Luau string ko auto-convert nahi karta; tonumber() use karo)":""}`);return false}
    return true}
  function bin(n){
    const op=n.op;
    if(op==="and"){const l=ex(n.l);const nr=condNar(n.l);const u=applyN(nr.t);const r=ex(n.r);u();
      if(l.k==="any")return AN;const f=falsy(l);return union([r,f])}
    if(op==="or"){const l=ex(n.l);const nr=condNar(n.l);const u=applyN(nr.f);const r=ex(n.r);u();
      if(l.k==="any")return AN;return union([truthy(l),r])}
    const l=ex(n.l),r=ex(n.r);
    if(["+","-","*","/","//","%","^"].includes(op)){
      const named=x=>x.k==="named"||x.k==="inst"||x.k==="gen"||x.k==="enumitem"||x.k==="any"||x.k==="unknown"||(x.k==="table"&&x.open);
      const lw=l,rw=r;
      if(named(lw)||named(rw)){
        if(lw.k==="named"&&rw.k==="named")return lw.n==="CFrame"&&rw.n==="Vector3"?rw:lw;
        if(lw.k==="named")return lw;if(rw.k==="named")return rw;return AN}
      const a=checkArith(op,lw,NUM,n,n.l),b=checkArith(op,rw,NUM,n,n.r);
      return NUM}
    if(op===".."){
      for(const[x,sub]of[[l,n.l],[r,n.r]]){
        if(x.k==="union"&&hasNil(x))nilAccess(x,sub,"'..' concat operand");
        const nn=x.k==="union"?removeNil(x):x;const mem=nn.k==="union"?nn.ts:[nn];
        if(mem.some(m=>m.k==="prim"&&(m.n==="boolean"||m.n==="nil")||m.k==="fn"||(m.k==="table"&&!m.open)))
          { if(!(x.k==="prim"&&x.n==="nil"&&nilOrigin(x)!=="user"&&!strict)) ERR("concat-type",n.tok,`'..' me ${show(widen(x))} operand valid nahi (string ya number chahiye; tostring() use karo)`)}}
      return STR}
    if(["<",">","<=",">="].includes(op)){
      const w1=widen(l),w2=widen(r);
      const p1=w1.k==="prim"?w1.n:null,p2=w2.k==="prim"?w2.n:null;
      if(p1&&p2&&p1!==p2||(p1&&["boolean","nil"].includes(p1))||(p2&&["boolean","nil"].includes(p2)))
        ERR("compare-type",n.tok,`'${op}' se ${show(w1)} aur ${show(w2)} compare nahi ho sakte`);
      return BOOL}
    return BOOL}
  // --- narrowing from conditions ---
  function condNar(c){
    const T_=[],F_=[];
    const reduce=(t,pred)=>{if(t.k==="any"||t.k==="unknown")return null;const mem=t.k==="union"?t.ts:[t];return mem.filter(pred)};
    switch(c.k){
      case"Paren":return condNar(c.e);
      case"Name":case"Index":{const key=pathKey(c);if(!key)break;const t=nar.has(key)?nar.get(key):(c.k==="Name"?(lookup(c.name)||{}).t:peekIndex(c));
        if(t&&t.k!=="any"){T_.push([key,truthy(t)]);F_.push([key,falsy(t)])}break}
      case"Un":if(c.op==="not"){const r=condNar(c.e);return{t:r.f,f:r.t}}break;
      case"MCall":{
        if(c.name==="IsA"&&c.args.length===1&&c.args[0].k==="Str"){const key=pathKey(c.o);const cls=c.args[0].v;
          if(key&&(CLS.has(cls)||CREATABLE_SET.has(cls)))T_.push([key,{k:"inst",n:cls}])}
        break}
      case"Bin":{
        if(c.op==="and"){const a=condNar(c.l),b=condNar(c.r);return{t:[...a.t,...b.t],f:[]}}
        if(c.op==="or"){const a=condNar(c.l),b=condNar(c.r);return{t:[],f:[...a.f,...b.f]}}
        if(c.op==="=="||c.op==="~="){
          let L=c.l,R=c.r;if(L.k==="Nil"){[L,R]=[R,L]}
          if(R.k==="Nil"){const key=pathKey(L);if(key){const t=nar.has(key)?nar.get(key):(L.k==="Name"?(lookup(L.name)||{}).t:peekIndex(L));
            if(t&&t.k!=="any"){const nn=removeNil(t);const eq=c.op==="==";(eq?T_:F_).push([key,NIL]);(eq?F_:T_).push([key,nn.k==="never"?t:nn])}}break}
          // typeof(x) == "string"
          if((L.k==="Call"&&L.f.k==="Name"&&(L.f.name==="typeof"||L.f.name==="type")&&L.args.length===1)&&R.k==="Str"){
            const key=pathKey(L.args[0]);if(!key)break;
            const t=nar.has(key)?nar.get(key):(L.args[0].k==="Name"?(lookup(L.args[0].name)||{}).t:peekIndex(L.args[0]));if(!t)break;
            const tn=R.v;const match=m=>{switch(tn){case"string":case"number":case"boolean":case"thread":return m.k==="prim"&&m.n===tn;case"nil":return m.k==="prim"&&m.n==="nil";case"table":return m.k==="table";case"function":return m.k==="fn";case"Instance":case"userdata":return m.k==="inst"||m.k==="named";default:return true}};
            const base=t.k==="any"||t.k==="unknown"?(["string","number","boolean","thread"].includes(tn)?prim(tn):null):null;
            const yes=base||(()=>{const m=reduce(t,match);return m&&union(m)})();
            const no=t.k==="any"||t.k==="unknown"?null:(()=>{const m=reduce(t,x=>!match(x));return m&&union(m)})();
            const eq=c.op==="==";if(yes)(eq?T_:F_).push([key,yes]);if(no)(eq?F_:T_).push([key,no])}}}}
    return{t:T_,f:F_}}
  function peekIndex(n){ // type of an expression without emitting diagnostics or recording hooks
    peekDepth++;let t;try{t=ex(n)}catch{t=AN}finally{peekDepth--}return t}
  // --- calls ---
  function cpath(n){if(n.k==="Name")return n.name;if(n.k==="Index"){const p=cpath(n.o);return p?p+"."+n.name:null}return null}
  function call(n){
    const path=cpath(n.f);
    if(path==="Instance.new"){return instNew(n)}
    if(path==="require"){return requireCall(n)}
    if(path==="setmetatable"&&n.args.length===2){
      const a0=ex(n.args[0]);const a1=ex(n.args[1]);let cls=null;
      if(a1.k==="table"&&a1.shape&&!a1.isInst)cls=a1;
      else if(n.args[1].k==="Table"){const it=n.args[1].items.find(i=>i.kind==="name"&&i.name==="__index");if(it&&it.v.k==="Name"){const x=ex(it.v);if(x.k==="table"&&x.shape&&!x.isInst)cls=x}}
      return cls?instOf(cls):AN}
    if(path==="error"||path==="assert"){n.args.forEach(a=>ex(a))}
    const ft=ex(n.f);
    if(path==="pcall"||path==="xpcall"){n.args.forEach(a=>{if(a.k==="Func")a.inline=true});pcallStack.push({unchecked:n===stmtCall});n.args.forEach(a=>ex(a));pcallStack.pop();return AN}
    if(path==="task.wait"||path==="wait")noteYield(n.tok,path+"()");
    if(path==="ipairs"||path==="pairs"){n.args.forEach(a=>ex(a));return AN}
    if(path==="typeof"||path==="type"){n.args.forEach(a=>ex(a));return STR}
    return applyCall(ft,n.args,n,path||"function")}
  function mcall(n){
    const ot=ex(n.o);
    if(CLIENT_M.has(n.name))noteCtx("client",n.tok,n.name);if(SERVER_M.has(n.name))noteCtx("server",n.tok,n.name);
    if(n.name==="GetService"&&ot.k==="inst"&&ot.n==="DataModel")return getService(n);
    if(ot.k==="union"){nilAccess(ot,n,`'${pathName(n.o)}':${n.name}()`)}
    const base=ot.k==="union"?removeNil(ot):ot;
    hookMCall(n,base);
    if(base.k==="inst"&&base.n==="DataModel"&&n.name==="FindService"){n.args.forEach(a=>ex(a));return AN}
    const ft=member(base,n.name,{tok:n.tok,o:n.o,k:"Index"},"call");
    if(base.k==="named"||base.k==="any"){n.args.forEach(a=>ex(a));return AN}
    const r=applyCall(ft,n.args,n,`${n.name}()`,true);
    if(base.k==="inst"){
      const a0=n.args[0];
      if((n.name==="FindFirstChildOfClass"||n.name==="FindFirstChildWhichIsA"||n.name==="FindFirstAncestorOfClass"||n.name==="FindFirstAncestorWhichIsA")&&a0&&a0.k==="Str"&&(CLS.has(a0.v)||CREATABLE_SET.has(a0.v)))return union([{k:"inst",n:a0.v},prim("nil",undefined,"api")]);
      if(n.name==="Clone")return{...base};
      if((n.name==="WaitForChild"||n.name==="FindFirstChild")&&a0&&a0.k==="Str"){const wn=t=>t.k==="inst"?{...t,rname:a0.v}:(t.k==="union"?union(t.ts.map(wn)):t);return wn(r)}}
    return r}
  function hookMCall(n,base){
    if(peekDepth>0)return;
    const nm=n.name;
    if(nm==="WaitForChild")noteYield(n.tok,"WaitForChild()");
    if(nm==="Wait"&&base.k==="signal")noteYield(n.tok,"signal:Wait()");
    if((nm==="InvokeServer"||nm==="InvokeClient")&&(base.k==="inst"||base.k==="any"))noteYield(n.tok,nm+"()");
    if(nm==="GetDescendants"&&hotDepth>0)WARN("perf-hot-traversal",n.tok,"Hot loop/per-frame callback me GetDescendants() — har tick poora tree traverse hota hai; cache karo ya tag/CollectionService use karo");
    // DataStore lints
    if(base.k==="inst"&&base.n==="DataStore"&&DSM.has(nm)){
      if(nm==="GetAsync")ds.get=ds.get||n.tok;if(nm==="SetAsync")ds.set=ds.set||n.tok;if(nm==="UpdateAsync")ds.update=true;
      if(nm!=="GetAsync"&&!ds.write)ds.write=n.tok;
      noteYield(n.tok,"DataStore:"+nm+"()");
      const pc=pcallStack[pcallStack.length-1];
      if(!pc)WARN("datastore-no-pcall",n.tok,`DataStore:${nm}() pcall ke bina — DataStore calls fail ho sakti hain (throttle/outage); pcall + retry use karo`);
      else if(pc.unchecked)WARN("datastore-pcall-unchecked",n.tok,"pcall ka result check nahi ho raha — DataStore fail hua to data silently lost hoga; `local ok, err = pcall(...)` check karo");
      if(loopDepth>0)INFO("datastore-in-loop",n.tok,`DataStore:${nm}() loop ke andar — request budget khatam ho sakta hai; batch/throttle (task.wait) karo`);
      const top=cbStack[cbStack.length-1];if(top&&top.hot)WARN("datastore-in-hot-callback",n.tok,`DataStore:${nm}() per-frame callback me — budget turant khatam hoga`)}
    // remotes
    const rk=()=>{const r=base.rname||lastName(n.o);return r?String(r).toLowerCase():null};
    if((nm==="FireServer"||nm==="FireClient"||nm==="FireAllClients"||nm==="InvokeServer"||nm==="InvokeClient")&&(base.k==="inst"||base.k==="any")){
      const key=rk();const dir=nm==="FireServer"||nm==="InvokeServer"?"server":"client";const skip=nm==="FireClient"||nm==="InvokeClient"?1:0;
      if(key)shared.calls.push({key,dir,args:n.args.slice(skip).map(a=>widen(peekIndex(a))),tok:n.tok,file:opts.file,kind:nm})}
    if(nm==="Connect"&&n.o.k==="Index"&&(n.o.name==="OnServerEvent"||n.o.name==="OnClientEvent")&&n.args[0]&&n.args[0].k==="Func"){
      const rb=peekIndex(n.o.o);const r=rb.rname||lastName(n.o.o);
      if(r){const server=n.o.name==="OnServerEvent";const f=n.args[0];const ps=f.params.map(p=>({name:p.name,t:p.type?rt(p.type):null,opt:p.type?hasNil(rt(p.type)):true}));
        shared.handlers.push({key:String(r).toLowerCase(),dir:server?"server":"client",params:server?ps.slice(1):ps,vararg:!!f.vararg,file:opts.file,tok:n.tok});
        if(server&&f.params.length>1){
          const names=f.params.slice(1).map(p=>p.name);const checked=new Set();
          walk(f.body,nd=>{if(nd.k==="Call"){const p=cpath(nd.f);if(p==="typeof"||p==="type"||p==="assert"||p==="tonumber"||p==="tostring")nd.args.forEach(a=>{if(a.k==="Name")checked.add(a.name)})}
            if(nd.k==="MCall"&&nd.name==="IsA"&&nd.o.k==="Name")checked.add(nd.o.name);
            if(nd.k==="Call"){const p=cpath(nd.f);if(p==="math.clamp"||p==="math.floor"||p==="math.max"||p==="math.min")nd.args.forEach(a=>{if(a.k==="Name")checked.add(a.name)})}});
          const un=names.filter(x=>!checked.has(x));
          if(un.length)INFO("remote-unvalidated",n.tok,`OnServerEvent: client se aaye params (${un.join(", ")}) ko server par validate karo (typeof/range check) — Luau type annotations runtime par enforce nahi hote, exploiter kuch bhi bhej sakta hai`)}}}
    // lifecycle
    if(base.k==="signal"&&(nm==="Connect"||nm==="ConnectParallel")){
      if(loopDepth>0&&n===stmtCall){
        const rootN=x=>x.k==="Name"?x.name:(x.k==="Index"?rootN(x.o):(x.k==="Paren"?rootN(x.e):null));
        const rn=rootN(n.o);const rb=rn?lookup(rn):null;
        const perItem=!rn||(rb&&rb.loopLevel>=loopDepth);   // receiver created inside the loop (e.g. each button) or unknown => normal
        if(!perItem)WARN("connect-in-loop",n.tok,"Loop ke andar ek hi object par Connect() — har iteration par naya connection banta hai (leak/duplicate handlers); Connect ko loop se bahar karo")}
      if(cbStack.length>0&&base.global){
        const cap=capOf(n);
        if(n===stmtCall)WARN("connection-leak",n.tok,`Event callback ke andar ${base.label} pe Connect() — har event par naya connection banega aur kabhi disconnect nahi hoga (player/character leave par leak). Connection ko variable me rakho aur Disconnect() karo${/PlayerRemoving/.test(src)?"":" (is file me PlayerRemoving cleanup bhi nahi hai)"}`);
        else if(cap&&!new RegExp("\\b"+cap+"\\s*:\\s*Disconnect\\s*\\(").test(src))INFO("connection-not-disconnected",n.tok,`'${cap}' connection kabhi Disconnect() nahi hota — event callback ke andar banne par leak ho sakta hai`)}}
  }
  function getService(n){
    const a=n.args[0];n.args.forEach(x=>ex(x));
    if(a&&a.k==="Str"){
      if(!SERVICE_SET.has(a.v)){const sg=suggest(a.v,SERVICE_LIST);const near=!!sg;
        (near||strict||DB_FULL?ERR:WARN)("unknown-service",a.tok,`'${a.v}' validator ki service list me nahi hai`+(sg?` — shayad '${sg}'? (typo lagta hai)`:" — spelling check karo (list official/complete nahi hai, isliye non-strict me sirf warning)"))}
      if(SERVER_SVC.has(a.v))noteCtx("server",a.tok,`GetService("${a.v}")`);if(CLIENT_SVC.has(a.v))noteCtx("client",a.tok,`GetService("${a.v}")`);
      return{k:"inst",n:a.v}}
    return{k:"inst",n:"Instance"}}
  function instNew(n){
    const a=n.args[0];n.args.forEach(x=>ex(x));
    if(!a)return AN;
    if(a.k==="Str"){
      if(!CREATABLE_SET.has(a.v)){
        const sg=suggest(a.v,CREATABLE);
        if(CLS.has(a.v)||SERVICE_SET.has(a.v))ERR("unknown-class",a.tok,`'${a.v}' Instance.new se create nahi hoti (service/non-creatable class)`);
        else (sg||strict||DB_FULL?ERR:WARN)("unknown-class",a.tok,`Unknown Roblox class '${a.v}' (validator ki creatable-class list me nahi)`+(sg?` — shayad '${sg}'? (typo lagta hai)`:" — spelling check karo (list official/complete nahi hai, isliye non-strict me sirf warning)"));
        return{k:"inst",n:"Instance"}}
      if(hotDepth>0)WARN("perf-hot-instance-new",n.tok,`Hot loop/per-frame callback me Instance.new("${a.v}") — har frame object banana expensive hai; pool/reuse karo`);
      return{k:"inst",n:a.v,fresh:true}}
    const w=widen(ex(a));if(w.k==="prim"&&w.n!=="string")ERR("arg-type",a.tok,`Instance.new ka argument string hona chahiye, ${show(w)} mila`);
    return{k:"inst",n:"Instance"}}
  function requireCall(n){
    const a=n.args[0];if(!a){ERR("arg-count",n.tok,"require() ko 1 argument chahiye (ModuleScript ya asset id)");return AN}
    n.args.forEach(x=>ex(x));
    if(opts.resolve){const nm=lastName(a);const exp=nm?opts.resolve(nm,a):null;if(exp)return exp}
    const t=ex(a);
    if(a.k==="Str"){if(!/^(\.{1,2}\/|@|\/)/.test(a.v))ERR("invalid-require",a.tok,`require("${a.v}") valid nahi — ModuleScript Instance (ya asset id number) chahiye, plain string nahi`)}
    else{const w=widen(t);if(w.k==="prim"&&(w.n==="boolean"||w.n==="nil"))ERR("invalid-require",a.tok,`require() ko ${w.n} nahi de sakte`);else if(w.k==="table"&&!w.open)ERR("invalid-require",a.tok,"require() ko table nahi de sakte")}
    return AN}
  function applyCall(ft,args,node,label,isMethod){
    if(ft.k==="union"){nilAccess(ft,node,`${label}`);ft=removeNil(ft)}
    if(ft.k!=="fn"||ft.any||!ft.params){args.forEach(a=>ex(a));return AN}
    if(ft.overloads)return overloadCall(ft,args,node,label);
    const ps=ft.params;const multiLast=isMulti(args[args.length-1]);
    const lbl=ft.label||label;
    const countCheck=ft.known||(ft.declared!==undefined&&(ft.allAnnotated||true));
    // arity
    if(!ft.vararg&&args.length>ps.length&&(ft.known||ft.declared!==undefined||ft.self)&&!(multiLast&&false)){
      ERR("arg-count",node.tok,`${lbl} ko ${ps.length} argument${ps.length===1?"":"s"} chahiye, ${args.length} diye gaye`)}
    const req=ps.filter(p=>!p.opt).length;
    if(args.length<req&&!multiLast&&(ft.known||ft.allAnnotated))ERR("arg-count",node.tok,`${lbl} ko kam se kam ${req} argument chahiye, ${args.length} diye gaye`);
    else if(!ft.known&&ft.declared!==undefined&&!ft.allAnnotated&&!multiLast&&!ft.vararg&&args.length<ps.length&&ps.length>0&&!ft.self&&ps.slice(args.length).some(p=>!p.softOpt))
      (strict?ERR:WARN)("arg-count",node.tok,`${lbl} ${ps.length} parameter leta hai par ${args.length} argument diye gaye — baaki nil honge${strict?"":" (non-strict me chalta hai, par check kar lo)"}`);
    // generics
    const gb=new Map();
    const inst_=t=>t.k==="gen"&&gb.has(t.n+t.id)?gb.get(t.n+t.id):t;
    args.forEach((a,i)=>{
      const p=ps[i]||(ft.vararg?{t:ft.vararg}:null);
      if(!p){ex(a);return}
      let exp=p.t;
      if(exp.k!=="gen"&&hasGen(exp)){ex(a);return}
      if(exp.k==="gen"){const at=widen(ex(a));const key=exp.n+exp.id;gb.set(key,gb.has(key)?union([gb.get(key),at]):at);return}
      const t=exArg(a,exp);
      if(!assignable(t,exp)){
        const calls=label;
        if(exp.k==="fn"&&exp.isCallback)ERR("arg-type",a.tok||node.tok,`${lbl} ko callback function chahiye, ${show(widen(t))} mila`);
        else reportMis("arg-type",a.tok||node.tok,t,exp,`${lbl}: argument ${i+1} ka type ${show(exp)} hona chahiye, ${show(t.k==="union"?t:widen(t))} mila`)}});
    // UpdateAsync callback shape / FireClient first arg
    if(lbl.endsWith(":UpdateAsync")&&args[1]&&args[1].k==="Func"&&args[1].params.length===0)WARN("callback-shape",args[1].tok,"UpdateAsync callback ko (oldValue) parameter lena chahiye");
    if(/^(RemoteEvent|UnreliableRemoteEvent):FireClient$/.test(lbl)&&args.length===0)ERR("arg-count","tok" in node?node.tok:node.tok,"FireClient ko pehla argument Player chahiye");
    if(/:FireServer$/.test(lbl)&&args[0]){const a0=args[0];if((a0.k==="Name"&&/^(player|plr|lp|localplayer)$/i.test(a0.name))||(a0.k==="Index"&&a0.name==="LocalPlayer"))WARN("remote-player-arg",a0.tok,"FireServer server ko player khud pass karta hai — player argument bhejna zaroori nahi (server pe pehla param already player hai)")}
    let r=ft.ret&&ft.ret.length?ft.ret[0]:AN;
    if(ft.gens&&r)r=substGen(r,gb);
    return r}
  function sigStr(f){return"("+f.params.map(p=>show(p.t)).join(", ")+(f.vararg?(f.params.length?", ":"")+"..."+show(f.vararg):"")+")"}
  function overloadCall(ft,args,node,label){
    const ts=args.map(a=>ex(a));const multiLast=isMulti(args[args.length-1]);
    for(const sg of ft.overloads){
      const ps=sg.params;const req=ps.filter(p=>!p.opt).length;
      if(!multiLast&&(args.length<req||(!sg.vararg&&args.length>ps.length)))continue;
      let ok=true;for(let i=0;i<ts.length&&ok;i++){const p=ps[i]||(sg.vararg?{t:sg.vararg}:null);if(!p){ok=!!multiLast;continue}if(!assignable(ts[i],p.t))ok=false}
      if(ok)return sg.ret&&sg.ret.length?sg.ret[0]:AN}
    ERR("no-overload",node.tok,`${ft.label||label}: ye argument types kisi overload se match nahi karte (${ts.map(t=>show(t.k==="union"?t:widen(t))).join(", ")}). Valid: ${ft.overloads.slice(0,5).map(sigStr).join(" | ")}${ft.overloads.length>5?" | ...":""}`);
    return ft.overloads[0].ret&&ft.overloads[0].ret.length?ft.overloads[0].ret[0]:AN}
  function hasGen(t){switch(t.k){case"gen":return true;case"union":return t.ts.some(hasGen);case"table":return!!(t.indexer&&hasGen(t.indexer.val))||[...t.props.values()].some(p=>hasGen(p.t));case"fn":return(t.params||[]).some(p=>hasGen(p.t))||(t.ret||[]).some(hasGen);default:return false}}
  function substGen(t,gb){
    if(t.k==="gen")return gb.has(t.n+t.id)?gb.get(t.n+t.id):AN;
    if(t.k==="union")return union(t.ts.map(x=>substGen(x,gb)));
    if(t.k==="table"&&t.indexer)return{...t,indexer:{key:t.indexer.key,val:substGen(t.indexer.val,gb)}};
    return t}
  // --- statements ---
  function terminates(b){
    const s=b[b.length-1];if(!s)return false;
    if(s.k==="Return"||s.k==="Break"||s.k==="Continue")return true;
    if(s.k==="ExprStat"&&s.e.k==="Call"&&s.e.f.k==="Name"&&s.e.f.name==="error")return true;
    if(s.k==="If"&&s.els)return s.blocks.every(terminates)&&terminates(s.els);
    return false}
  const walk=(n,fn)=>{if(!n||typeof n!=="object")return;if(Array.isArray(n)){n.forEach(x=>walk(x,fn));return}if(fn(n)===false)return;for(const k in n){if(k==="tok"||k==="dot"||k==="vt")continue;const v=n[k];if(v&&typeof v==="object")walk(v,fn)}};
  function raceCheck(stmts,i){
    const s0=stmts[i];if(s0.e.k!=="Call")return;const path=cpath(s0.e.f);
    if(path!=="task.spawn"&&path!=="task.defer"&&path!=="task.delay")return;
    const fa=s0.e.args.find(a=>a.k==="Func");if(!fa)return;
    const declared=new Set(fa.params.map(p=>p.name));const assigned=new Set();
    walk(fa.body,nd=>{if(nd.k==="Local")nd.names.forEach(x=>declared.add(x.name));if(nd.k==="LocalFunc")declared.add(nd.name);if(nd.k==="Assign")nd.targets.forEach(t=>{if(t.k==="Name")assigned.add(t.name)})});
    const outer=[...assigned].filter(nm=>!declared.has(nm)&&lookup(nm));
    if(!outer.length)return;
    const reported=new Set();
    for(let j=i+1;j<stmts.length;j++){
      const st=stmts[j];let yielded=false;
      walk(st,nd=>{
        if(nd.k==="Func")return false;
        if(nd.k==="Assign"){walk(nd.values,x=>{if(x.k==="Name"&&outer.includes(x.name)&&!reported.has(x.name)){reported.add(x.name);WARN("async-race",x.tok,`'${x.name}' ko ${path} ke andar set kiya gaya hai par yahin turant read ho raha hai — spawned function baad me chalta hai (race); task.wait/event/signal se synchronize karo`)}});nd.targets.forEach(t=>{if(t.k!=="Name")walk(t,()=>{})});return false}
        if(nd.k==="Name"&&outer.includes(nd.name)&&!reported.has(nd.name)){reported.add(nd.name);WARN("async-race",nd.tok,`'${nd.name}' ko ${path} ke andar set kiya gaya hai par yahin turant read ho raha hai — spawned function baad me chalta hai (race); task.wait/event/signal se synchronize karo`)}
        if(nd.k==="Call"){const p=cpath(nd.f);if(p==="task.wait"||p==="wait")yielded=true}
        if(nd.k==="MCall"&&nd.name==="Wait")yielded=true});
      if(yielded)break}}
  function block(stmts){
    const persist=[];let warned=false;
    for(let i=0;i<stmts.length;i++){
      const s=stmts[i];
      if(i>0&&!warned&&(stmts[i-1].k==="Break"||stmts[i-1].k==="Continue"||(stmts[i-1].k==="ExprStat"&&stmts[i-1].e.k==="Call"&&stmts[i-1].e.f.k==="Name"&&stmts[i-1].e.f.name==="error"))){WARN("unreachable-code",s.tok,"Unreachable code — upar break/continue/error ke baad ye kabhi nahi chalega");warned=true}
      const post=stat(s);if(post&&post.length)persist.push(applyN(post));
      if(s.k==="ExprStat")raceCheck(stmts,i)}
    for(const u of persist.reverse())u()}
  function stat(s){
    switch(s.k){
      case"Local":{
        const decl=s.names.map(n=>n.type?rt(n.type):null);
        const vals=s.values;const vts=[];
        vals.forEach((v,i)=>{
          localCap=v.k==="MCall"?{node:v,name:s.names[i]&&s.names[i].name}:null;
          const d=decl[i];
          if(d){vts.push(checkAssign(v,d,s.names[i].tok,`local ${s.names[i].name}`))}
          else vts.push(ex(v));localCap=null});
        s.names.forEach((n,i)=>{
          let t;
          if(decl[i])t=decl[i];
          else if(i<vts.length&&!(i>=vals.length)){const w=widen(vts[i]);t=(w.k==="prim"&&w.n==="nil")?AN:w;if(vals[i]&&vals[i].k==="Table")t=vts[i]}
          else t=AN;
          bind(n.name,t,{decl:!!decl[i],tok:n.tok,inferred:!decl[i]})});
        return null}
      case"LocalFunc":{
        const placeholder={k:"fn",params:[],ret:null,known:false,declared:!!s.func.ret,any:true};
        const b=bind(s.name,placeholder,{tok:s.tok});
        const f=fnLiteral(s.func);b.t=f;return null}
      case"FuncStat":{
        const tg=s.target;
        if(tg.k==="Name"){const f0={k:"fn",any:true};const b=lookup(tg.name);if(!b)bind(tg.name,f0,{tok:tg.tok,global:true})}
        else{const base=ex(tg.o);if(base.k==="table"&&base.shape&&s.func.isMethod)s.func.selfType=instOf(base)}
        const f=fnLiteral(s.func);
        if(tg.k==="Index"){const base=peekIndex(tg.o);if(base.k==="table"&&base.shape&&!base.isInst)base.props.set(tg.name,{t:f})}
        if(tg.k==="Name"){const b=lookup(tg.name);if(b&&b.global)b.t=f}
        return null}
      case"Assign":return assign(s);
      case"ExprStat":stmtCall=s.e;ex(s.e);stmtCall=null;return null;
      case"If":{
        const accF=[];const undoAll=[];let post=null;
        for(let i=0;i<s.conds.length;i++){
          ex(s.conds[i]);
          const nr=condNar(s.conds[i]);
          const uF=applyN(accF);const u=applyN(nr.t);pushS();block(s.blocks[i]);popS();u();uF();
          accF.push(...nr.f)}
        if(s.els){const u=applyN(accF);pushS();block(s.els);popS();u()}
        else if(s.blocks.every(terminates))post=accF;
        return post}
      case"While":{ex(s.cond);const nr=condNar(s.cond);const u=applyN(nr.t);const hotL=s.cond.k==="Bool"&&s.cond.v===true;loopDepth++;if(hotL)hotDepth++;pushS();block(s.body);popS();loopDepth--;if(hotL)hotDepth--;u();return nr.f.length&&!hasBreak(s.body)?nr.f:null}
      case"Repeat":{loopDepth++;pushS();block(s.body);ex(s.cond);popS();loopDepth--;return null}
      case"Do":pushS();block(s.body);popS();return null;
      case"NumFor":{
        for(const e of[s.start,s.stop,s.step]){if(!e)continue;const t=widen(ex(e));if(t.k==="prim"&&t.n!=="number")ERR("for-type",e.tok||s.tok,`numeric for me ${show(t)} nahi chalega — number chahiye`)}
        loopDepth++;pushS();bind(s.name,NUM,{tok:s.tok,param:true});block(s.body);popS();loopDepth--;return null}
      case"GenFor":{
        const e0=s.exprs[0];let kt=AN,vt=AN;
        if(e0.k==="Call"&&e0.f.k==="Name"&&(e0.f.name==="ipairs"||e0.f.name==="pairs")&&e0.args.length===1){
          e0.args.forEach(()=>0);const at=ex(e0.args[0]);ex(e0.f);
          const a=at.k==="union"?removeNil(at):at;
          if(at.k==="union"&&hasNil(at))nilAccess(at,e0.args[0],`${e0.f.name}() argument`);
          if(a.k==="table"&&a.indexer){vt=a.indexer.val;kt=e0.f.name==="ipairs"?NUM:a.indexer.key}}
        else s.exprs.forEach(e=>ex(e));
        {const isTrav=e=>e.k==="MCall"&&(e.name==="GetDescendants"||e.name==="GetChildren")||(e.k==="Call"&&e.f.k==="Name"&&(e.f.name==="ipairs"||e.f.name==="pairs")&&e.args[0]&&isTrav(e.args[0]));
          if(isTrav(e0)&&loopDepth>0)WARN("perf-nested-traversal",s.tok,"Loop ke andar GetDescendants()/GetChildren() ka traversal — nested loop O(n²) ban sakta hai; result cache karo ya CollectionService/tag use karo")}
        loopDepth++;pushS();s.names.forEach((n,i)=>bind(n.v,i===0?kt:(i===1?vt:AN),{tok:n,param:true}));block(s.body);popS();loopDepth--;return null}
      case"Return":{
        const f=fnInfo.stack[fnInfo.stack.length-1];
        if(!f){s.values.forEach((v,i)=>{const t=ex(v);if(i===0)exportType=t});return null}
        const ret=f.ret;const vals=s.values;
        if(ret){
          vals.forEach((v,i)=>{
            if(ret[i]){const d=ret[i];const t=(v.k==="Table"&&d.k==="table")?(()=>{ex(v,d);return d})():ex(v,d);
              if(!assignable(t,d)){
                if(d.k==="gen")ERR("generic-mismatch",v.tok||s.tok,`Return value ('${show(widen(t))}') generic type ${d.n} se compatible nahi hai`);
                else reportMis("return-type",v.tok||s.tok,t,d,`Function ${show(t.k==="union"?t:widen(t))} return karta hai par declared return type ${show(d)} hai`)}}
            else{ex(v);if(!isMulti(vals[vals.length-1])&&i>=ret.length)ERR("return-count",v.tok||s.tok,`Function ${ret.length} value return karne ke liye declare hua hai, ${vals.length} return ho rahi hain`)}});
          if(vals.length<ret.length&&!isMulti(vals[vals.length-1])){const missing=ret.slice(vals.length).filter(r=>!hasNil(r)&&r.k!=="any");if(missing.length)ERR("return-count",s.tok,`Function ${ret.length} value return karne ke liye declare hua hai, ${vals.length} return ho rahi hain`)}}
        else{vals.forEach((v,i)=>{const t=ex(v);if(i===0)f.returns.push(t)});if(!vals.length)f.returns.push(NIL)}
        return null}
      case"TypeDecl":return null;
      case"Break":case"Continue":return null}
    return null}
  const hasBreak=b=>JSON.stringify(b,(k,v)=>k==="tok"||k==="dot"?undefined:v).includes('"k":"Break"');
  function assign(s){
    const compound=s.op!=="=";
    s.targets.forEach((tg,i)=>{
      const v=s.values[i];
      localCap=v&&v.k==="MCall"?{node:v,name:null}:null;
      if(tg.k==="Name"){
        const b=lookup(tg.name);
        if(compound){const lt=b?(nar.get("b"+b.id)||b.t):AN;const rt_=ex(v);
          if(s.op==="..="){}else if(b){const op=s.op.slice(0,-1);if(lt.k!=="any"&&lt.k!=="named"){const u=widen(lt);if(u.k==="prim"||u.k==="union"){checkArith(op,u,NUM,s,tg);if(rt_.k!=="named")checkArith(op,widen(rt_),NUM,s,v)}}}
          return}
        if(b&&b.decl&&v){
          const d=b.t;const t=checkAssignQuiet(v,d,s.tok,tg.name,"assign-mismatch");
          invalidate("b"+b.id);
          if(d.k==="union"||hasNil(d)){const w=widen(t);if(w.k!=="any")nar.set("b"+b.id,w)}
          return}
        if(b&&b.inferred&&v&&strict){const d=b.t;const t=ex(v);const w=widen(t);if(d.k==="prim"&&w.k==="prim"&&!(w.n==="nil")&&d.n!==w.n)ERR("assign-mismatch",s.tok,`'${tg.name}' ka type ${show(d)} hai, usme ${show(w)} assign nahi kar sakte`);invalidate("b"+b.id);return}
        if(v)ex(v);if(b)invalidate("b"+b.id);return}
      if(tg.k==="Index"){
        const ot=ex(tg.o);
        let pt=null;const base=ot.k==="union"?removeNil(ot):ot;
        if(ot.k==="union")nilAccess(ot,tg,`'${pathName(tg.o)}'.${tg.name}`);
        if(base.k==="inst"){
          const r=lookupMember(base.n,tg.name);
          if(r&&r.m&&r.m.kind==="prop")pt=r.m.t;
          else if(r&&r.m&&r.m.kind==="method")ERR("assign-method",tg.tok,`${base.n}.${tg.name} method hai, usme value assign nahi ho sakti`);
          else if(!r||(!r.unknownClass&&!r.m)){const c=CLS.get(base.n);if(base.fresh&&c&&c.full&&!knownLower(base.n,tg.name)){const all=[];for(const x of chain(base.n))if(x)for(const k of x.members.keys())all.push(k);const sg=suggest(tg.name,all);ERR("unknown-member",tg.tok,`${base.n} me '${tg.name}' naam ka member nahi hai (validator ki ${base.n} member list me nahi)`+(sg?` — shayad '${sg}'?`:""))}}}
        else if(base.k==="table"){const p=base.props.get(tg.name);if(p&&!base.shape)pt=p.t;else if(!p&&base.indexer&&base.indexer.key.k==="prim"&&base.indexer.key.n==="string")pt=base.indexer.val;
          if(base.shape&&!compound&&v&&tg.name!=="__index"){const vt0=ex(v);const w=widen(vt0);const old=base.props.get(tg.name);
            if(w.k==="fn"||old===undefined){base.props.set(tg.name,{t:(w.k==="fn"||w.k==="table"&&w.shape&&false)?w:(w.k==="prim"&&w.n==="nil"?AN:w)})}
            else if(old&&tkey(old.t)!==tkey(w))base.props.set(tg.name,{t:AN});
            const key=pathKey(tg);if(key)invalidate(key);return}}
        if(compound){if(v)ex(v);return}
        if(v&&v.k==="Func"&&(tg.name==="OnServerInvoke"||tg.name==="OnClientInvoke")){
          const r=(base.rname)||lastName(tg.o);
          if(r){const server=tg.name==="OnServerInvoke";const ps=v.params.map(p=>({name:p.name,t:p.type?rt(p.type):null,opt:p.type?hasNil(rt(p.type)):true}));
            shared.handlers.push({key:String(r).toLowerCase(),dir:server?"server":"client",params:server?ps.slice(1):ps,vararg:!!v.vararg,file:opts.file,tok:tg.tok})}}
        if(v){
          if(pt&&base.k==="inst"){const t=checkAssignProp(v,pt,tg,base);}
          else if(pt){checkAssign(v,pt,tg.tok,`${pathName(tg)}`,"assign-mismatch")}
          else ex(v)}
        const key=pathKey(tg);if(key)invalidate(key);
        return}
      if(tg.k==="IndexE"){ex(tg.o);ex(tg.e);if(v)ex(v)}});
    return null}
  function checkAssignQuiet(v,d,tok,name,rule){
    if(v.k==="Table"&&(d.k==="table"||(d.k==="union"&&d.ts.some(x=>x.k==="table")))){const tt=d.k==="union"?d.ts.find(x=>x.k==="table"):d;tt.label=name;ex(v,d);return d}
    const t=ex(v,d);
    if(!assignable(t,d))reportMis(rule,tok,t,d,`'${name}' ka type ${show(d)} hai, usme ${show(t.k==="union"?t:widen(t))} assign nahi kar sakte`);
    return t}
  function checkAssignProp(v,pt,tg,base){
    const t=ex(v,pt);
    if(!assignable(t,pt))reportMis("property-type",tg.tok,t,pt,`${base.n}.${tg.name} ko ${show(pt)} chahiye, ${show(t.k==="union"?t:widen(t))} mila`);
    return t}
  pushS();
  block(ast);
  // DataStore file-level
  if(ds.write&&/PlayerRemoving/.test(src)&&!/BindToClose/.test(src))WARN("datastore-no-bindtoclose",ds.write,"PlayerRemoving me save ho raha hai par game:BindToClose nahi hai — server shutdown par last players ka data save nahi hoga");
  if(ds.set&&ds.get&&!ds.update)INFO("datastore-setasync-race",ds.set,"GetAsync → modify → SetAsync pattern race condition de sakta hai (do servers ek saath) — read-modify-write ke liye UpdateAsync use karo");
  // client/server context
  const guard=/\bIs(Client|Server)\s*\(/.test(src);
  if(ctxKind==="client")ctxUse.server.forEach(u=>ERR("server-api-in-client",u.tok,`${u.what} server-only hai — client (LocalScript) me kaam nahi karega`));
  else if(ctxKind==="server")ctxUse.client.forEach(u=>ERR("client-api-in-server",u.tok,u.what==="LocalPlayer"?"Players.LocalPlayer server par nil hota hai — server Script me use nahi hota":`${u.what} client-only hai — server Script me kaam nahi karega`));
  else if(!ctxKind&&ctxUse.client.length&&ctxUse.server.length&&!guard){
    const c=ctxUse.client[0],sv=ctxUse.server[0];
    WARN("mixed-context",sv.tok,`Is script me client-only API (${c.what}, line ${c.tok.line}) aur server-only API (${sv.what}) dono hain — ek hi Script/LocalScript dono jagah nahi chal sakti (ModuleScript ho ya IsClient() se guard ho to theek). Context pakka batane ke liye context="client"/"server" do ya \`--@context client\` comment likho.`)}
  return{diags,mode,ran:true,exportType,ctxKind}}

class PErr{constructor(t,m){this.t=t;this.m=m}}

function validate1(src,rules=[],opts={}){
  const{T,E,clean}=lex(src);
  const errors=[...E],warnings=[];
  const stats={lines:src.split("\n").length,tokens:T.length-1,functions:0,locals:0,maxDepth:0};
  let p=0,sc=[new Map()],fn={vararg:true,loops:0},depth=0,yields=0,sawExit=false;
  const at=(t,rule,message,severity)=>({line:t.line,col:t.col,rule,severity,message});
  const pk=(o=0)=>T[Math.min(p+o,T.length-1)];
  const nx=()=>{const t=T[p];if(t.t!=="eof")p++;return t};
  const is=v=>{const t=pk();return(t.t==="kw"||t.t==="sym")&&t.v===v};
  const eat=v=>is(v)?nx():null;
  const desc=t=>t.t==="eof"?"end of file":`'${t.t==="str"?t.raw:t.v}'`;
  const fail=(m,t=pk())=>{throw new PErr(t,m)};
  const need=(v,open)=>{if(is(v))return nx();fail(`Expected '${v}'${open?` (to close '${open.v}' from line ${open.line})`:""}, got ${desc(pk())}`)};
  const nameTok=()=>{const t=pk();if(t.t!=="id")fail(`Expected a name, got ${desc(t)}`);return nx()};
  const find=n=>{for(let i=sc.length-1;i>=0;i--)if(sc[i].has(n))return sc[i].get(n);return null};
  const flush=m=>{for(const[n,v]of m)if(!v.used&&!v.param&&n[0]!=="_")warnings.push(at(v.tok,"unused-local",`Local '${n}' declare hua par kabhi read nahi hua`,"info"))};
  const push=()=>{sc.push(new Map());depth++;stats.maxDepth=Math.max(stats.maxDepth,depth)};
  const pop=()=>{flush(sc.pop());depth--};
  const declare=(t,o={})=>{
    if(!o.param&&t.v!=="_"){const e=find(t.v);if(e)warnings.push(at(t,"shadow",`'${t.v}' shadow ho raha hai (pehle line ${e.tok.line} par declare)`,"info"))}
    sc[sc.length-1].set(t.v,{tok:t,used:false,...o});stats.locals++};
  const use=t=>{const v=find(t.v);if(v){v.used=true;return}if(!GLOBALS.has(t.v))warnings.push(at(t,"undefined-global",`'${t.v}' define nahi hai (undefined global)`,"warning"))};
  const assign=t=>{if(!find(t.v)&&!GLOBALS.has(t.v))warnings.push(at(t,"global-assign",`'${t.v}' global ban raha hai — 'local' lagana tha?`,"warning"))};

  // ---- types (parsed and skipped) ----
  const skipBal=(o,c)=>{let d=0;do{const t=nx();if(t.t==="eof")fail("Unclosed type expression",t);if(t.t==="sym"){if(t.v===o)d++;else if(t.v===c)d--}}while(d>0)};
  const skipType=()=>{
    const one=()=>{const t=pk();
      if(is("(")){skipBal("(",")");if(is("->")){nx();skipType()}}
      else if(is("{"))skipBal("{","}");
      else if(is("...")){nx();skipType()}
      else if(t.t==="id"){nx();if(t.v==="typeof"&&is("("))skipBal("(",")");else{while(is(".")){nx();nameTok()}if(is("<"))skipBal("<",">")}}
      else if(t.t==="str"||(t.t==="kw"&&["nil","true","false"].includes(t.v)))nx();
      else fail(`Type expected, got ${desc(t)}`)};
    one();while(is("|")||is("&")||is("?")){const o=nx();if(o.v!=="?")one()}};

  // ---- expressions ----
  const interp=t=>{for(const m of t.raw.matchAll(/\{([^{}]*)\}/g))for(const id of m[1].matchAll(/(?<![.\w])[A-Za-z_]\w*/g))if(!KW.has(id[0]))use({v:id[0],line:t.line,col:t.col})};
  const args=()=>{let s=null;
    if(is("(")){nx();const a=pk(),b=pk(1);if(a.t==="str"&&(b.v===")"||b.v===","))s=a;if(!is(")")){expr();while(eat(","))expr()}need(")")}
    else if(pk().t==="str")s=nx();
    else table();
    return s};
  const onCall=(path,s)=>{
    if(YIELD.has(path.split(/[.:]/).pop()))yields++;
    if(s&&s.raw[0]!=="`"){
      if(path.endsWith(":GetService")&&!SERVICES.has(s.v))warnings.push(at(s,"unknown-service",`'${s.v}' known Roblox service nahi lagta (spelling?)`,"warning"));
      if(path==="Instance.new"&&!CLASSES.has(s.v))warnings.push(at(s,"unknown-class",`Instance.new('${s.v}') — class name check karo`,"info"))}};
  const suffixed=()=>{
    let k="exp",path="",t=pk();
    if(t.t==="id"){nx();use(t);k="name";path=t.v}
    else if(is("(")){nx();expr();need(")")}
    else fail(`Unexpected ${desc(t)}`);
    for(;;){
      if(is(".")){nx();path+="."+nameTok().v;k="index"}
      else if(is("[")){nx();expr();need("]");path="";k="index"}
      else if(is(":")){nx();path+=":"+nameTok().v;const s=args();onCall(path,s);path="";k="call"}
      else if(is("(")||pk().t==="str"||is("{")){const s=args();onCall(path,s);path="";k="call"}
      else break}
    return k};
  const table=()=>{
    need("{");
    while(!is("}")){
      if(is("[")){nx();expr();need("]");need("=");expr()}
      else if(pk().t==="id"&&pk(1).v==="="&&pk(1).t==="sym"){nx();nx();expr()}
      else expr();
      if(!eat(",")&&!eat(";"))break}
    need("}")};
  const ifexpr=()=>{nx();expr();need("then");expr();while(is("elseif")){nx();expr();need("then");expr()}need("else");expr()};
  const simple=()=>{
    const t=pk();
    if(t.t==="num")nx();
    else if(t.t==="str"){nx();if(t.raw[0]==="`")interp(t)}
    else if(t.t==="kw"&&(t.v==="nil"||t.v==="true"||t.v==="false"))nx();
    else if(is("...")){if(!fn.vararg)fail("'...' sirf vararg function me allowed hai");nx()}
    else if(is("{"))table();
    else if(is("function")){const f=nx();funcbody(f,false)}
    else if(is("if"))ifexpr();
    else suffixed();
    while(is("::")){nx();skipType()}};
  const expr=(lim=0)=>{
    const t=pk();
    if((t.t==="kw"&&t.v==="not")||(t.t==="sym"&&(t.v==="-"||t.v==="#"))){nx();expr(8)}else simple();
    for(;;){const o=pk(),b=(o.t==="kw"||o.t==="sym")&&BIN[o.v];if(!b||b[0]<=lim)break;nx();expr(b[1])}};
  const exprlist=()=>{expr();while(eat(","))expr()};

  // ---- functions & statements ----
  const funcbody=(open,self)=>{
    stats.functions++;
    if(is("<"))skipBal("<",">");
    need("(");
    const saved=fn;fn={vararg:false,loops:0};push();
    if(self)declare({v:"self",line:open.line,col:open.col},{used:true,param:true});
    const seen=new Set();
    if(!is(")")){do{
      if(is("...")){nx();fn.vararg=true;if(eat(":"))skipType();break}
      const t=nameTok();
      if(seen.has(t.v))errors.push(at(t,"duplicate-param",`Duplicate parameter '${t.v}'`,"error"));
      seen.add(t.v);declare(t,{param:true});
      if(eat(":"))skipType();
    }while(eat(","))}
    need(")");
    if(eat(":"))skipType();
    block(["end"]);need("end",open);pop();fn=saved};
  const block=terms=>{
    for(;;){
      const t=pk();
      if(t.t==="eof"||(t.t==="kw"&&terms.includes(t.v)))return;
      if(t.t==="kw"&&t.v==="return"){
        nx();sawExit=true;
        const n=pk();
        if(!(n.t==="eof"||(n.t==="kw"&&["end","else","elseif","until"].includes(n.v))||is(";")))exprlist();
        eat(";");
        const m=pk();
        if(!(m.t==="eof"||(m.t==="kw"&&terms.includes(m.v))))fail("'return' block ka last statement hona chahiye",m);
        return}
      stat()}};
  const loopBody=(t,inf,decl)=>{
    fn.loops++;push();if(decl)decl();
    const y=yields,e=sawExit;sawExit=false;
    block(["end"]);need("end",t);pop();fn.loops--;
    if(inf&&yields===y&&!sawExit)warnings.push(at(t,"infinite-loop","'while true' me yield (task.wait) nahi hai — script freeze/timeout ho sakti hai","warning"));
    sawExit=e||sawExit};
  const typedecl=()=>{if(pk().v==="export")nx();nx();nameTok();if(is("<"))skipBal("<",">");need("=");skipType()};
  const localstat=()=>{
    nx();
    if(is("function")){nx();const n=nameTok();declare(n);funcbody({v:"function",line:n.line,col:n.col},false);return}
    const names=[];
    do{const n=nameTok();if(eat(":"))skipType();names.push(n)}while(eat(","));
    if(eat("="))exprlist();
    names.forEach(n=>declare(n))};
  const forstat=t=>{
    nx();const n1=nameTok();
    if(is("=")){nx();expr();need(",");expr();if(eat(","))expr();need("do");loopBody(t,false,()=>declare(n1,{param:true}))}
    else{
      const names=[n1];while(eat(","))names.push(nameTok());
      need("in");exprlist();need("do");
      loopBody(t,false,()=>names.forEach(n=>declare(n,{param:true})))}};
  const exprstat=()=>{
    const t=pk();
    const isAsgn=x=>x.t==="sym"&&(x.v==="="||x.v===","||COMP.has(x.v));
    const tgt=()=>{const a=pk(),b=pk(1);if(a.t==="id"&&isAsgn(b)){nx();return{k:"name",t:a}}return{k:suffixed()}};
    const f=tgt();
    if(f.k==="call"&&!isAsgn(pk()))return;
    if(f.k!=="name"&&!isAsgn(pk()))fail("Ye expression statement nahi ho sakta (sirf function call allowed hai)",t);
    const ts=[f];while(eat(","))ts.push(tgt());
    for(const x of ts)if(x.k!=="name"&&x.k!=="index")fail("Invalid assignment target",t);
    if(COMP.has(pk().v)&&pk().t==="sym"){nx();expr();for(const x of ts)if(x.k==="name")use(x.t);return}
    need("=");exprlist();
    for(const x of ts)if(x.k==="name")assign(x.t)};
  const stat=()=>{
    const t=pk();
    if(is(";")){nx();return}
    if(is("@")){nx();nameTok();return stat()}
    if(t.t==="kw"){
      switch(t.v){
        case"local":return localstat();
        case"function":{
          nx();const n=nameTok();let m=false;
          while(is(".")){nx();nameTok()}
          if(is(":")){nx();nameTok();m=true}
          return funcbody({v:"function",line:t.line,col:t.col},m)}
        case"if":{
          nx();expr();need("then");push();block(["elseif","else","end"]);pop();
          while(is("elseif")){nx();expr();need("then");push();block(["elseif","else","end"]);pop()}
          if(eat("else")){push();block(["end"]);pop()}
          need("end",t);return}
        case"while":{nx();const inf=pk().v==="true"&&pk(1).v==="do";expr();need("do");return loopBody(t,inf)}
        case"for":return forstat(t);
        case"repeat":{nx();fn.loops++;push();block(["until"]);need("until",t);expr();pop();fn.loops--;return}
        case"do":{nx();push();block(["end"]);need("end",t);pop();return}
        case"break":nx();if(!fn.loops)fail("'break' loop ke bahar hai",t);sawExit=true;return;
        default:fail(`Unexpected '${t.v}' (extra 'end' ya missing opener?)`)}}
    if(t.t==="id"){
      if(t.v==="continue"&&!["=","(",".",":","[",","].includes(pk(1).v)){nx();if(!fn.loops)fail("'continue' loop ke bahar hai",t);return}
      if(t.v==="export"&&pk(1).v==="type"){typedecl();return}
      if(t.v==="type"&&pk(1).t==="id"&&(pk(2).v==="="||pk(2).v==="<")){typedecl();return}}
    exprstat()};

  let parsed=false;
  try{block([]);if(pk().t!=="eof")fail(`Unexpected ${desc(pk())}`);parsed=true}
  catch(e){if(!(e instanceof PErr))throw e;errors.push(at(e.t,"syntax",e.m,"error"))}
  if(parsed)flush(sc[0]);
  let exp_=null;
  const analysis={mode:"nonstrict",typeCheck:"skipped",reason:parsed?undefined:"syntax errors present"};
  if(parsed){
    try{
      const a=analyze(T,src,opts);analysis.mode=a.mode;analysis.context=a.ctxKind||opts.context||null;exp_=a.exportType||null;
      if(a.ran){
        analysis.typeCheck="ran";
        for(let i=warnings.length-1;i>=0;i--)if(warnings[i].rule==="unknown-class"||warnings[i].rule==="unknown-service")warnings.splice(i,1);
        errors.push(...a.diags.error);warnings.push(...a.diags.warning);warnings.push(...a.diags.info)}
      else{analysis.reason=a.reason||"--!nocheck";analysis.typeCheck="skipped"}}
    catch(e){analysis.typeCheck="skipped";analysis.reason="internal analyzer error: "+String(e&&e.message||e)}}

  for(const r of rules){
    let re;try{re=new RegExp(r.regex,"g")}catch{continue}
    let m;
    while((m=re.exec(clean))){
      const pre=clean.slice(0,m.index),line=pre.split("\n").length,col=m.index-pre.lastIndexOf("\n");
      (r.severity==="error"?errors:warnings).push({line,col,rule:r.id,severity:r.severity,message:r.message});
      if(m[0]==="")re.lastIndex++}}
  const by=(a,b)=>a.line-b.line||(a.col||0)-(b.col||0);
  errors.sort(by);warnings.sort(by);
  const info=warnings.filter(w=>w.severity==="info"),warns=warnings.filter(w=>w.severity!=="info");
  stats.errors=errors.length;stats.warnings=warns.length;stats.info=info.length;
  const res={valid:errors.length===0,errors,warnings:warns,info,stats,analysis};
  Object.defineProperty(res,"_export",{value:exp_,enumerable:false});
  return res;
}



const TYPE_RULES=new Set("type-mismatch arith-type return-type arg-type arg-count assign-mismatch nil-access invalid-cast missing-field unknown-field generic-mismatch concat-type compare-type for-type no-overload return-count invalid-length index-primitive property-type".split(" "));
const API_RULES=new Set("unknown-member unknown-class unknown-service unknown-enum-item assign-method invalid-require".split(" "));
const ARCH_RULES=new Set("server-api-in-client client-api-in-server mixed-context".split(" "));
const normMod=n=>String(n).split(/[\\/]/).pop().replace(/\.(client|server|module)\.(luau|lua)$/i,"").replace(/\.(luau|lua)$/i,"");
function validate(src,rules=[],opts={}){
  const modules=opts.modules&&typeof opts.modules==="object"?opts.modules:{};
  const names=Object.keys(modules);
  const shared={handlers:[],calls:[],stack:[],results:new Map()};
  const index=new Map();for(const n of names)index.set(normMod(n),n);
  const resolve=nm=>{
    const key=index.has(nm)?nm:[...index.keys()].find(k=>k.toLowerCase()===String(nm).toLowerCase());
    if(!key)return null;const orig=index.get(key);
    if(shared.results.has(orig))return shared.results.get(orig)._export||AN;
    if(shared.stack.includes(orig))return AN;
    shared.stack.push(orig);
    const mctx=/\.client\./i.test(orig)?"client":/\.server\./i.test(orig)?"server":"module";
    const r=validate1(modules[orig],rules,{file:orig,shared,resolve,context:mctx,name:orig});
    shared.stack.pop();shared.results.set(orig,r);return r._export||AN};
  const main=validate1(src,rules,{...opts,modules:undefined,shared,resolve});
  for(const n of names)resolve(normMod(n));
  const errors=[...main.errors],warnings=[...main.warnings],info=[...main.info];
  const modSummary={};
  for(const[orig,r]of shared.results){
    const tag=l=>l.map(d=>d.file?d:{...d,file:orig});
    errors.push(...tag(r.errors));warnings.push(...tag(r.warnings));info.push(...tag(r.info));
    modSummary[orig]={valid:r.errors.length===0,errors:r.errors.length,warnings:r.warnings.length,exports:r._export?show(r._export):"unknown",analysis:r.analysis.typeCheck}}
  for(const d of contractDiags(shared)){(d.severity==="error"?errors:warnings).push(d)}
  const by=(a,b)=>{const fa=a.file||"",fb=b.file||"";return fa<fb?-1:fa>fb?1:(a.line-b.line||(a.col||0)-(b.col||0))};
  errors.sort(by);warnings.sort(by);info.sort(by);
  const stats={...main.stats,errors:errors.length,warnings:warnings.length,info:info.length};
  const all=[...errors,...warnings];
  const has=(set)=>errors.some(e=>set.has(e.rule)||e.rule.startsWith("remote-contract"));
  const ran=main.analysis.typeCheck==="ran";
  const synErr=errors.some(e=>e.rule==="syntax");
  const area=(set,partial)=>errors.some(e=>set.has(e.rule))?"FAIL":(ran?partial:"SKIPPED");
  const verdict={
    overall:errors.length?"FAIL":(ran?"PASS_PARTIAL":"INCOMPLETE"),
    meaning:errors.length?"Validator ko errors mile — code fix karo.":(ran?"Supported checks me koi error nahi mila. Ye guarantee NAHI hai ki code Roblox me sahi chalega (official compiler/full API nahi hai).":"Type/API analysis chali hi nahi ("+(main.analysis.reason||"skipped")+") — result incomplete hai."),
    syntax:synErr?"FAIL":"PASS",
    scope:warnings.some(w=>w.rule==="undefined-global"||w.rule==="global-assign")?"WARN":"PASS",
    types:area(TYPE_RULES,"PARTIAL"),
    robloxApi:area(API_RULES,DB_FULL?"FULL_DB":"PARTIAL"),
    architecture:errors.some(e=>ARCH_RULES.has(e.rule))?"FAIL":(warnings.some(w=>ARCH_RULES.has(w.rule))?"WARN":"HEURISTIC"),
    remotes:errors.some(e=>e.rule.startsWith("remote-contract"))?"FAIL":"ANNOTATED_ONLY",
    dataStore:warnings.some(w=>w.rule.startsWith("datastore"))?"WARN":"HEURISTIC",
    performance:warnings.some(w=>w.rule.startsWith("perf-"))?"WARN":"HEURISTIC",
    lifecycle:warnings.some(w=>w.rule.startsWith("connect")||w.rule.startsWith("async")||w.rule.startsWith("yield"))?"WARN":"HEURISTIC",
    crossModule:names.length?"CHECKED":"NOT_CHECKED (modules parameter nahi diya)",
    security:warnings.concat(info).some(w=>w.rule==="remote-unvalidated")?"WARN":"HEURISTIC",
    officialCompiler:false};
  const res={valid:errors.length===0,errors,warnings,info,stats,verdict,analysis:main.analysis,capabilities:CAPABILITIES};
  if(names.length)res.modules=modSummary;
  return res}

const CAPABILITIES={
  officialLuauCompiler:false,
  syntax:true,
  scope:true,
  deprecatedApiRules:true,
  controlFlow:"partial (break/continue placement, unreachable code after break/continue/error)",
  typeChecking:"partial (annotation-driven + local inference of literals/API returns; not a full solver)",
  nilAnalysis:"partial (optional types + narrowing via if/and/or/not/==nil/typeof/IsA)",
  generics:"basic (<T> params/returns, call-site inference)",
  tableTypes:"partial (annotated table/array/dictionary types, literal field checks)",
  oopMetatable:"basic (setmetatable/__index class pattern: methods + fields assigned in constructor/methods)",
  overloads:"basic (built-in table of overloaded APIs; user-defined function intersections not supported)",
  crossModule:"supported only when the `modules` parameter is provided (require() resolved by module name)",
  remoteContracts:"annotated OnServerEvent/OnClientEvent/OnServerInvoke params vs FireServer/FireClient/Invoke args (same file or provided modules)",
  clientServer:"exact when context/--@context/file name is given; heuristic warning otherwise",
  dataStoreLints:"heuristic",
  asyncLints:"heuristic (spawn/defer/delay assignment race, yield in per-frame callback)",
  performanceLints:"heuristic",
  lifecycleLints:"heuristic (connection leaks, connect in loop)",
  securityLints:"heuristic (unvalidated remote args only)",
  robloxApiChecking:DB_FULL?"full (generated from official API dump: "+CLS.size+" classes)":"partial ("+CLS.size+" classes built in; run build-api-db.mjs with Roblox's API-Dump.json for the full database)",
  fullLuauTypeInference:false,
  fullRobloxApi:DB_FULL,
  notSupported:["official Luau compiler / full type solver","runtime behaviour (races, data loss) cannot be proven statically","DataStore session locking verification","exploit/security review beyond remote-arg validation hints","cross-file analysis for files not passed in `modules`"]};
const rules={"version":1,"rules":[{"id":"screeninsets-topbar-strip","regex":"ScreenInsets\\s*=\\s*Enum\\.ScreenInsets\\.TopbarSafeInsets","severity":"warning","message":"ScreenInsets = TopbarSafeInsets ScreenGui ko sirf top-bar ki patli patti tak seemit karta hai: normal/full-screen UI sliver me collapse ho jaata hai aur ScrollingFrame sab clip kar deta hai. ScreenInsets line hata do (default CoreUISafeInsets = top bar ke neeche) aur IgnoreGuiInset=false rakho. Device par test karo."},{"id":"deprecated-wait","regex":"(?<![.\\w:])wait\\s*\\(","severity":"warning","message":"wait() deprecated hai; task.wait() use karo"},{"id":"deprecated-spawn","regex":"(?<![.\\w:])spawn\\s*\\(","severity":"warning","message":"spawn() deprecated hai; task.spawn() use karo"},{"id":"deprecated-delay","regex":"(?<![.\\w:])delay\\s*\\(","severity":"warning","message":"delay() deprecated hai; task.delay() use karo"},{"id":"lowercase-connect","regex":":connect\\s*\\(","severity":"warning","message":":connect deprecated; :Connect use karo"},{"id":"lowercase-disconnect","regex":":disconnect\\s*\\(","severity":"warning","message":":disconnect deprecated; :Disconnect use karo"},{"id":"lowercase-wait","regex":":wait\\s*\\(","severity":"warning","message":":wait() deprecated; :Wait() use karo"},{"id":"deprecated-remove","regex":":Remove\\s*\\(","severity":"warning","message":":Remove() deprecated; :Destroy() use karo"},{"id":"instance-new-parent","regex":"Instance\\.new\\s*\\([^)]*,","severity":"warning","message":"Instance.new ka 2nd (parent) argument avoid karo; properties set karke last me .Parent set karo"},{"id":"game-workspace","regex":"\\bgame\\.Workspace\\b","severity":"info","message":"workspace global ya game:GetService('Workspace') use karo"},{"id":"fenv","regex":"\\b(getfenv|setfenv)\\b","severity":"warning","message":"getfenv/setfenv Luau me discouraged hain, optimizations todte hain"},{"id":"loadstring","regex":"\\bloadstring\\b","severity":"warning","message":"loadstring default me disabled hota hai (ServerScriptService.LoadStringEnabled)"},{"id":"table-getn","regex":"\\btable\\.getn\\b","severity":"error","message":"table.getn Luau me nahi hai; #t use karo"},{"id":"global-unpack","regex":"(?<![.\\w])unpack\\s*\\(","severity":"warning","message":"unpack() ki jagah table.unpack() use karo"},{"id":"tick","regex":"\\btick\\s*\\(","severity":"info","message":"tick() deprecated; os.time(), os.clock() ya workspace:GetServerTimeNow() use karo"},{"id":"while-true","regex":"while\\s+true\\s+do\\b","severity":"info","message":"while true do loop me task.wait() zaroor ho, warna script exhaust ho jayegi"}]};
const H={"access-control-allow-origin":"*","access-control-allow-methods":"GET,POST,OPTIONS","access-control-allow-headers":"content-type,accept,mcp-session-id,mcp-protocol-version,authorization","content-type":"application/json"};
const J=(o,s=200)=>new Response(JSON.stringify(o),{status:s,headers:H});

// ---- MCP (Streamable HTTP, stateless JSON responses) at POST /mcp ----
const MAXC=200000;
function cleanOpts(A){
  const o={};
  if(A&&A.modules&&typeof A.modules==="object"&&!Array.isArray(A.modules)){
    const m={};let total=0,n=0;
    for(const[k,v]of Object.entries(A.modules)){if(typeof v!=="string")continue;n++;total+=v.length;if(n>20||total>400000)return{error:"modules: max 20 files / 400KB total"};m[String(k).slice(0,120)]=v}
    o.modules=m}
  if(A&&["client","server","module","shared"].includes(A.context))o.context=A.context;
  if(A&&typeof A.name==="string")o.name=A.name.slice(0,200);
  return o}
const TOOL={name:"validate_external_luau",description:"Validate exact Roblox Luau source: syntax, scope, deprecated APIs, partial type/nil/generic/Roblox-API analysis, remote contracts, client/server checks and heuristic DataStore/performance/lifecycle lints. Optional: pass `modules` ({name: source}) so require() resolves cross-module types and remote contracts; pass `context` (client|server|module) for client/server API checks. Returns {valid, errors, warnings, info, stats, verdict, analysis, capabilities}. valid=true only means no errors found within the supported analysis (see verdict) - NOT the official Luau compiler.",inputSchema:{type:"object",properties:{code:{type:"string",description:"Exact Luau source, max 200KB."},modules:{type:"object",additionalProperties:{type:"string"},description:"Optional other files: {ModuleName: source}. Used to resolve require() and remote handlers."},context:{type:"string",enum:["client","server","module"],description:"Optional script context (LocalScript=client, Script=server, ModuleScript=module)."},name:{type:"string",description:"Optional file name, e.g. Main.client.lua"}},required:["code"]}};
const rpcOk=(id,result)=>({jsonrpc:"2.0",id,result});
const rpcErr=(id,code,message)=>({jsonrpc:"2.0",id,error:{code,message}});
const toolText=(o,isError=false)=>({content:[{type:"text",text:JSON.stringify(o,null,2)}],isError});
function mcpHandle(m){
  if(!m||typeof m!=="object"||Array.isArray(m)||m.jsonrpc!=="2.0"||typeof m.method!=="string")return rpcErr(m&&m.id!==undefined?m.id:null,-32600,"Invalid Request");
  if(m.id===undefined||m.id===null)return null; // notification: no response
  const p=m.params||{};
  switch(m.method){
    case"initialize":return rpcOk(m.id,{protocolVersion:p.protocolVersion||"2025-03-26",capabilities:{tools:{listChanged:false}},serverInfo:{name:"luau-validator-bridge",version:"4.0.0"}});
    case"ping":return rpcOk(m.id,{});
    case"tools/list":return rpcOk(m.id,{tools:[TOOL]});
    case"resources/list":return rpcOk(m.id,{resources:[]});
    case"prompts/list":return rpcOk(m.id,{prompts:[]});
    case"tools/call":{
      if(p.name!==TOOL.name)return rpcErr(m.id,-32602,"Unknown tool: "+p.name);
      const code=p.arguments&&p.arguments.code;
      if(typeof code!=="string")return rpcOk(m.id,toolText({error_code:"EXTERNAL_VALIDATION_BAD_INPUT",message:"'code' must be a string."},true));
      if(code.length>MAXC)return rpcOk(m.id,toolText({error_code:"EXTERNAL_VALIDATION_INPUT_TOO_LARGE",message:"Input exceeds 200KB."},true));
      const co=cleanOpts(p.arguments);if(co.error)return rpcOk(m.id,toolText({error_code:'EXTERNAL_VALIDATION_BAD_INPUT',message:co.error},true));
      try{return rpcOk(m.id,toolText(validate(code,rules.rules,co)))}
      catch(e){return rpcOk(m.id,toolText({error_code:"VALIDATOR_INTERNAL_ERROR",message:String(e&&e.message||e)},true))}}
    default:return rpcErr(m.id,-32601,"Method not found: "+m.method)}}
async function mcpRoute(req){
  if(req.method!=="POST")return new Response(JSON.stringify({error:"Use POST /mcp (Streamable HTTP, JSON-RPC)"}),{status:405,headers:{...H,allow:"POST, OPTIONS"}});
  let body;try{body=await req.json()}catch{return J(rpcErr(null,-32700,"Parse error"),400)}
  if(Array.isArray(body)){
    const out=body.map(mcpHandle).filter(x=>x!==null);
    return out.length?J(out):new Response(null,{status:202,headers:H})}
  const out=mcpHandle(body);
  return out===null?new Response(null,{status:202,headers:H}):J(out)}
export default{async fetch(req){
  const u=new URL(req.url);
  if(req.method==="OPTIONS")return new Response(null,{headers:H});
  if(u.pathname==="/rules")return J(rules);
  if(u.pathname==="/capabilities")return J({capabilities:CAPABILITIES,classes:CLS.size,creatableClasses:CREATABLE.length,services:SERVICE_LIST.length});
  if(u.pathname==="/health")return J({status:"ok",service:"luau-validator",mcp:"/mcp"});
  if(u.pathname==="/mcp")return mcpRoute(req);
  if(u.pathname==="/validate"){
    let code=u.searchParams.get("code");
    let co={};
    if(req.method==="POST"){try{const body=await req.json();code=body.code;co=cleanOpts(body)}catch{return J({error:"JSON body {code} chahiye"},400)}}
    else{const c=u.searchParams.get("context");if(c)co=cleanOpts({context:c})}
    if(co.error)return J({error:co.error},400);
    if(typeof code!=="string"||code.length>200000)return J({error:"code missing ya bahut bada (max 200KB)"},400);
    return J(validate(code,rules.rules,co))}
  return J({endpoints:["POST /validate {code}","GET /validate?code=","GET /rules","GET /health","GET /capabilities","POST /mcp (MCP Streamable HTTP)"]})}};
